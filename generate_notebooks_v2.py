"""
Generate 4 self-contained Jupyter Notebooks (no external utils).
"""
from pathlib import Path
import nbformat as nbf
from string import Template

NB_DIR = Path(__file__).resolve().parent / 'notebooks'
OUTPUT_DIR = 'outputs'
MODEL_DIR = 'models'
PATH_SENTIMENT = 'data/processed/analisis_sentimen.comments_sentiment.csv'
PATH_PREPROC = 'data/processed/analisis_sentimen.comments_preprocessed.csv'

NB_KERNEL = {
    'display_name': '.venv (3.12.7.final.0)',
    'language': 'python', 'name': 'python3',
}

def md(s): return nbf.v4.new_markdown_cell(s)
def code(s): return nbf.v4.new_code_cell(s)
def t(tpl, **kw): return Template(tpl).safe_substitute(**kw)

# =============================================================
# Utility functions block (embedded in every notebook)
# =============================================================
UTILS_BLOCK = '''from __future__ import annotations

import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.classification import LogisticRegression, NaiveBayes
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import (
    CountVectorizer, IDF, NGram, RegexTokenizer,
    StringIndexer, StringIndexerModel, VectorAssembler,
)
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ============================================================
# CONSTANTS
# ============================================================
SEED = 42
TRAIN_RATIO = 0.80
TEXT_COL = 'text_final'
LABEL_COL = 'sentiment'
VALID_LABELS = ('positif', 'netral', 'negatif')
PROJECT_ROOT = Path.cwd().resolve()
if PROJECT_ROOT.name == 'notebooks':
    PROJECT_ROOT = PROJECT_ROOT.parent
OUTPUT_DIR = PROJECT_ROOT / '${OUTPUT}'
MODEL_DIR = PROJECT_ROOT / '${MODEL}'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def create_spark_session(app_name: str = 'sentiment-training') -> SparkSession:
    spark = SparkSession.builder \\
        .appName(app_name) \\
        .master('local[*]') \\
        .config('spark.sql.adaptive.enabled', 'true') \\
        .config('spark.driver.memory', '8g') \\
        .config('spark.sql.shuffle.partitions', '8') \\
        .config('spark.default.parallelism', '8') \\
        .config('spark.serializer', 'org.apache.spark.serializer.KryoSerializer') \\
        .getOrCreate()
    # Fix: Hadoop chmod issue on Windows (winutils.exe not available)
    spark._jsc.hadoopConfiguration().set('fs.file.impl', 'org.apache.hadoop.fs.RawLocalFileSystem')
    return spark
    # Note: sesuaikan driver.memory dengan RAM komputer (8g atau 16g)


def stratified_split(df: DataFrame, ratio: float = TRAIN_RATIO, seed: int = SEED):
    window_spec = Window.partitionBy(LABEL_COL).orderBy(F.rand(seed))
    df_ranked = df.withColumn('_rn', F.row_number().over(window_spec))
    label_counts = {r[LABEL_COL]: r['count'] for r in df.groupBy(LABEL_COL).count().collect()}
    train_cond = None
    test_cond = None
    for lbl in VALID_LABELS:
        cnt = label_counts.get(lbl, 0)
        if cnt == 0:
            continue
        train_limit = int(round(cnt * ratio))
        c_train = (F.col(LABEL_COL) == lbl) & (F.col('_rn') <= train_limit)
        c_test = (F.col(LABEL_COL) == lbl) & (F.col('_rn') > train_limit)
        train_cond = c_train if train_cond is None else train_cond | c_train
        test_cond = c_test if test_cond is None else test_cond | c_test
    train_df = df_ranked.filter(train_cond).drop('_rn').cache()
    test_df = df_ranked.filter(test_cond).drop('_rn').cache()
    return train_df, test_df


def build_pipeline(model_name: str, **kwargs) -> Pipeline:
    tokenizer = RegexTokenizer(
        inputCol=TEXT_COL, outputCol='tokens',
        pattern=r'\\s+', gaps=True, minTokenLength=2,
    )
    label_indexer = StringIndexer(
        inputCol=LABEL_COL, outputCol='label_index', handleInvalid='keep'
    )
    ngram = NGram(n=2, inputCol='tokens', outputCol='bigrams')
    name = model_name.lower().strip()
    vocab_uni = kwargs.get('vocab_uni', 8000)
    vocab_bi = kwargs.get('vocab_bi', 6000)
    min_df = kwargs.get('min_df', 3.0)
    cv_uni = CountVectorizer(inputCol='tokens', outputCol='uni_feat', vocabSize=vocab_uni, minDF=min_df, minTF=1)
    cv_bi = CountVectorizer(inputCol='bigrams', outputCol='bi_feat', vocabSize=vocab_bi, minDF=min_df, minTF=1)

    if name in ('logistic_regression', 'lr', 'logistic regression'):
        assembler = VectorAssembler(inputCols=['uni_feat', 'bi_feat'], outputCol='raw_feat')
        idf = IDF(inputCol='raw_feat', outputCol='features', minDocFreq=2)
        clf = LogisticRegression(
            featuresCol='features', labelCol='label_index', predictionCol='pred_index',
            maxIter=kwargs.get('max_iter', 300), regParam=kwargs.get('reg_param', 0.05),
            elasticNetParam=kwargs.get('elastic_net', 0.15), family='multinomial', tol=1e-4,
        )
        stages = [tokenizer, ngram, cv_uni, cv_bi, assembler, idf, label_indexer, clf]
    elif name in ('naive_bayes', 'nb', 'naive bayes'):
        use_bigrams = kwargs.get('use_bigrams', False)
        clf = NaiveBayes(
            featuresCol='features', labelCol='label_index', predictionCol='pred_index',
            modelType='multinomial', smoothing=kwargs.get('smoothing', 0.5),
        )
        if use_bigrams:
            assembler = VectorAssembler(inputCols=['uni_feat', 'bi_feat'], outputCol='features')
            stages = [tokenizer, ngram, cv_uni, cv_bi, assembler, label_indexer, clf]
        else:
            assembler = VectorAssembler(inputCols=['uni_feat'], outputCol='features')
            stages = [tokenizer, cv_uni, assembler, label_indexer, clf]
    else:
        raise ValueError(f'Model tidak dikenal: {model_name}')
    return Pipeline(stages=stages)


def compute_metrics(predictions: DataFrame) -> dict:
    total = predictions.count()
    def _eval(metric):
        return MulticlassClassificationEvaluator(
            labelCol='label_index', predictionCol='pred_index', metricName=metric
        ).evaluate(predictions)
    accuracy = _eval('accuracy')
    f1_weighted = _eval('f1')
    precision_weighted = _eval('weightedPrecision')
    recall_weighted = _eval('weightedRecall')

    cm_rows = {
        (r[LABEL_COL], r['pred_label']): r['cnt']
        for r in predictions.groupBy(LABEL_COL, 'pred_label').agg(F.count('*').alias('cnt')).collect()
    }
    per_class = {}
    macro_p = macro_r = macro_f1 = 0.0
    for lbl in VALID_LABELS:
        tp = cm_rows.get((lbl, lbl), 0)
        fp = sum(cm_rows.get((actual, lbl), 0) for actual in VALID_LABELS if actual != lbl)
        fn = sum(cm_rows.get((lbl, pred), 0) for pred in VALID_LABELS if pred != lbl)
        support = tp + fn
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / support if support > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        per_class[lbl] = {'precision': round(p, 6), 'recall': round(r, 6), 'f1': round(f1, 6), 'support': support}
        macro_p += p; macro_r += r; macro_f1 += f1
    n = len(VALID_LABELS)
    cm_dict = {actual: {pred: cm_rows.get((actual, pred), 0) for pred in VALID_LABELS} for actual in VALID_LABELS}
    return {
        'total_samples': total, 'accuracy': round(accuracy, 6),
        'f1_weighted': round(f1_weighted, 6), 'f1_macro': round(macro_f1 / n, 6),
        'precision_weighted': round(precision_weighted, 6), 'precision_macro': round(macro_p / n, 6),
        'recall_weighted': round(recall_weighted, 6), 'recall_macro': round(macro_r / n, 6),
        'per_class': per_class, 'confusion_matrix': cm_dict,
    }


def map_prediction_labels(df, fitted_pipeline):
    # StringIndexerModel always at stages[-2] for both LR and NB pipelines
    si_model = fitted_pipeline.stages[-2]
    lbls = list(si_model.labels)
    when_expr = None
    for i, lbl in enumerate(lbls):
        cond = F.col('pred_index').cast('int') == i
        when_expr = F.when(cond, F.lit(lbl)) if when_expr is None else when_expr.when(cond, F.lit(lbl))
    return df.withColumn('pred_label', when_expr)


def train_and_evaluate(model_key, model_display, train_df, test_df) -> dict:
    print(f'\\n>>> Training: {model_display} ...', flush=True)
    for col_name in ("tokens",):
        if col_name in train_df.columns: train_df = train_df.drop(col_name)
        if col_name in test_df.columns:  test_df = test_df.drop(col_name)
    pipeline_obj = build_pipeline(model_key)
    stages = pipeline_obj.getStages()
    is_lr = model_key.lower() in ('logistic_regression', 'lr', 'logistic regression')

    if is_lr:
        label_counts = train_df.groupBy(LABEL_COL).count().collect()
        total = sum(r['count'] for r in label_counts)
        n_class = len(label_counts)
        weight_dict = {r[LABEL_COL]: total / (n_class * r['count']) for r in label_counts}
        print('Class weights (inverse frequency):')
        for k, v in weight_dict.items(): print(f'  {k} -> {v:.4f}')
        mapping = F.create_map(*[x for kv in weight_dict.items() for x in (F.lit(kv[0]), F.lit(float(kv[1])))])
        train_df_w = train_df.withColumn('class_weight', mapping[F.col(LABEL_COL)])
        feat_stages = stages[:-1]
        feat_model = Pipeline(stages=feat_stages).fit(train_df_w)
        train_feat = feat_model.transform(train_df_w).cache()
        test_feat = feat_model.transform(test_df).cache()
        base_lr = stages[-1]; base_lr.setWeightCol('class_weight')
        param_grid = ParamGridBuilder() \\
            .addGrid(base_lr.regParam, [0.01, 0.05, 0.1]) \\
            .addGrid(base_lr.elasticNetParam, [0.0, 0.15, 0.5]).build()
        evaluator = MulticlassClassificationEvaluator(labelCol='label_index', predictionCol='pred_index', metricName='f1')
        cv = CrossValidator(estimator=base_lr, estimatorParamMaps=param_grid, evaluator=evaluator, numFolds=3, seed=SEED, parallelism=4)
        # parallelism=4 => 4 model fit berjalan paralel (default 1 sangat lambat)
        cv_model = cv.fit(train_feat)
        best_lr = cv_model.bestModel
        print(f'  Best LR params: regParam={best_lr.getRegParam():.4f}, elasticNet={best_lr.getElasticNetParam():.4f}')
        train_pred = best_lr.transform(train_feat)
        test_pred = best_lr.transform(test_feat)
        si_model = feat_model.stages[-1]
        labels = list(si_model.labels)
        when_expr = None
        for i, lbl in enumerate(labels):
            cond = F.col('pred_index').cast('int') == i
            when_expr = F.when(cond, F.lit(lbl)) if when_expr is None else when_expr.when(cond, F.lit(lbl))
        train_pred = train_pred.withColumn('pred_label', when_expr)
        test_pred = test_pred.withColumn('pred_label', when_expr)
        model_obj = cv_model
    else:
        fitted = Pipeline(stages=stages).fit(train_df)
        si_model = fitted.stages[-2]
        labels = list(si_model.labels)
        when_expr = None
        for i, lbl in enumerate(labels):
            cond = F.col('pred_index').cast('int') == i
            when_expr = F.when(cond, F.lit(lbl)) if when_expr is None else when_expr.when(cond, F.lit(lbl))
        train_pred = fitted.transform(train_df).withColumn('pred_label', when_expr)
        test_pred = fitted.transform(test_df).withColumn('pred_label', when_expr)
        model_obj = fitted

    train_metrics = compute_metrics(train_pred)
    test_metrics = compute_metrics(test_pred)
    print(f'  Accuracy : {test_metrics["accuracy"]:.4f}')
    print(f'  F1 Score : {test_metrics["f1_weighted"]:.4f}')
    print(f'  Precision: {test_metrics["precision_weighted"]:.4f}')
    print(f'  Recall   : {test_metrics["recall_weighted"]:.4f}')
    return {'model': model_obj, 'train_prediction': train_pred, 'test_prediction': test_pred,
            'train': train_metrics, 'test': test_metrics}


def save_predictions_csv(predictions_df, filepath: str):
    pdf = predictions_df.select('comment_id', TEXT_COL, LABEL_COL, 'pred_label').toPandas()
    pdf.to_csv(filepath, index=False, encoding='utf-8')
    print(f'  Prediksi disimpan: {filepath} ({len(pdf)} baris)')


print('Library dan fungsi berhasil dimuat.')'''

EVAL_BLOCK = '''print(f'{"Model":<22} {"Accuracy":>10} {"F1-W":>10} {"F1-M":>10} {"Prec-W":>10} {"Rec-W":>10}')
print('-' * 76)
for name, res in results.items():
    m = res['test']
    print(f'{name:<22} {m["accuracy"]:>10.4f} {m["f1_weighted"]:>10.4f} {m["f1_macro"]:>10.4f} {m["precision_weighted"]:>10.4f} {m["recall_weighted"]:>10.4f}')

print(f'\\n{"Per-Kelas F1":22} {"positif":>12} {"netral":>12} {"negatif":>12}')
print('-' * 62)
for name, res in results.items():
    pc = res['test']['per_class']
    print(f'{name:<22} {pc.get("positif",{}).get("f1",0):>12.4f} {pc.get("netral",{}).get("f1",0):>12.4f} {pc.get("negatif",{}).get("f1",0):>12.4f}')

print(f'\\n  Confusion Matrix:')
for name, res in results.items():
    cm = res['test']['confusion_matrix']
    print(f'\\n  {name}:')
    print(f'    {"":12}' + ''.join(f'{p:>10}' for p in VALID_LABELS))
    for actual in VALID_LABELS:
        print(f'    {actual:<12}' + ''.join(f'{cm[actual].get(p,0):>10}' for p in VALID_LABELS))

print(f'\\nPer-class detail:')
for name, res in results.items():
    print(f'\\n  {name}:')
    print(f'  {"Label":<12} {"Precision":>10} {"Recall":>10} {"F1":>10} {"Support":>10}')
    print(f'  {"-"*56}')
    for lbl, m in res['test']['per_class'].items():
        print(f'  {lbl:<12} {m["precision"]:>10.4f} {m["recall"]:>10.4f} {m["f1"]:>10.4f} {m["support"]:>10}')'''

SAVE_EVAL_BLOCK = '''eval_data = {}
for name, res in results.items():
    eval_data[name] = {'train_metrics': res['train'], 'test_metrics': res['test']}
with open(eval_path, 'w', encoding='utf-8') as f:
    json.dump(eval_data, f, ensure_ascii=False, indent=2)
print(f'Evaluasi: {eval_path}')
for name, res in results.items():
    key = 'lr' if 'Logistic' in name else 'nb'
    save_predictions_csv(res['test_prediction'], str(OUTPUT_DIR / f'{csv_prefix}_{key}.csv'))'''


def make_nb(title, cells):
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        'kernelspec': NB_KERNEL,
        'language_info': {'name': 'python', 'version': '3.12.7'},
    }
    nb['cells'] = [md(title)] + cells
    return nb


# =============================================================
# Phase 1
# =============================================================
def make_phase1():
    return make_nb('# Phase 1: Training 2.000 Data Berlabel (80/20)', [
        md('''Melatih Logistic Regression (CrossValidator) dan Naive Bayes pada 2.000 data.
Split 80/20 stratified. Model terbaik dipilih berdasarkan F1-macro.
Output: model tersimpan, evaluasi JSON, prediksi CSV.'''),
        md('## 1. Import & Inisialisasi'),
        code(t(UTILS_BLOCK, OUTPUT=OUTPUT_DIR, MODEL=MODEL_DIR)),
        code("spark = create_spark_session('phase1-2000-80-20')\nspark.sparkContext.setLogLevel('WARN')\nprint(f'Spark: {spark.sparkContext.master}')"),
        md('## 2. Load Data'),
        code(t("csv_path = str(PROJECT_ROOT / '${P}')\nprint(f'Membaca: {csv_path}')\nraw_df = spark.read.option('header','true').option('multiLine','true').option('escape','\"').csv(csv_path)\nprint(f'Baris: {raw_df.count()}')", P=PATH_SENTIMENT)),
        md('## 3. Distribusi Label'),
        code("raw_df.groupBy(LABEL_COL).count().orderBy(LABEL_COL).show(truncate=False)\ntotal = raw_df.count()\nfor r in raw_df.groupBy(LABEL_COL).count().orderBy(LABEL_COL).collect():\n    print(f'  {r[LABEL_COL]:10s}: {r[\"count\"]:5d} ({r[\"count\"]/total*100:.1f}%)')"),
        md('## 4. Stratified Split 80/20'),
        code("train_df, test_df = stratified_split(raw_df)\nprint(f'Train: {train_df.count()}  |  Test: {test_df.count()}')"),
        md('## 5. Training Kedua Model'),
        code(t("""MODELS = [('logistic_regression','Logistic Regression'),('naive_bayes','Naive Bayes')]
results = {}
best_model_key = None; best_model_score = -1.0; best_model_display = ''
for mk, md in MODELS:
    t0 = time.time()
    res = train_and_evaluate(mk, md, train_df, test_df)
    results[md] = res
    print(f'  Waktu: {time.time()-t0:.2f} dtk')
    f1m = res['test']['f1_macro']
    if f1m > best_model_score:
        best_model_score = f1m; best_model_key = mk; best_model_display = md
print(f'\\n>>> Model terbaik: {best_model_display} (F1-macro={best_model_score:.4f})'""")),
        md('## 6. Evaluasi Lengkap'),
        code(EVAL_BLOCK),
        md('## 7. Simpan Info Model Terbaik'),
        code(t("""# PipelineModel.save() gagal di Windows (Hadoop chmod issue).
# Cukup simpan metadata — Phase 2 akan retrain pipeline dari 2000 data.
info = {'best_model_key': best_model_key, 'best_model_display': best_model_display,
        'best_f1_macro': best_model_score, 'timestamp': datetime.now(timezone.utc).isoformat()}
with open(str(MODEL_DIR / 'best_model_info.json'), 'w') as f: json.dump(info, f, indent=2)
print(f'Model info saved: {info["best_model_display"]} (F1-macro={best_model_score:.4f})')""")),
        md('## 8. Simpan Evaluasi & Prediksi'),
        code(t("eval_path = str(OUTPUT_DIR / 'evaluation_phase1_2000_80_20.json')\ncsv_prefix = 'predictions_phase1_2000_80_20'\n" + SAVE_EVAL_BLOCK, OUTPUT=OUTPUT_DIR)),
        md('## 9. Stop Spark'),
        code("spark.stop()\nprint('Phase 1 selesai.')"),
    ])


# =============================================================
# Phase 2
# =============================================================
def make_phase2():
    return make_nb('# Phase 2: Auto-labeling Data Baru', [
        md('Memuat model terbaik dari Phase 1, memprediksi label `comments_preprocessed.csv`. Output: CSV + statistik JSON.'),
        md('## 1. Import & Inisialisasi'),
        code(t(UTILS_BLOCK, OUTPUT=OUTPUT_DIR, MODEL=MODEL_DIR)),
        code("spark = create_spark_session('phase2-auto-labeling')\nspark.sparkContext.setLogLevel('WARN')\nprint(f'Spark: {spark.sparkContext.master}')"),
        md('## 2. Load Info & Retrain Pipeline'),
        code(t("""# PipelineModel tidak bisa disimpan via .save() di Windows.
# Strategi: simpan metadata (best_model_key), retrain dari 2000 data.
info_path = str(MODEL_DIR / 'best_model_info.json')
if not os.path.exists(info_path): raise FileNotFoundError(f'Info not found: {info_path}')
with open(info_path) as f: info = json.load(f)
print(f'Model: {info["best_model_display"]} (F1-macro={info["best_f1_macro"]:.4f})')
sentiment_csv = str(PROJECT_ROOT / 'data/processed/analisis_sentimen.comments_sentiment.csv')
train_data = spark.read.option('header','true').option('multiLine','true').option('escape','"').csv(sentiment_csv)
print(f'Train data: {train_data.count()} baris')
loaded = build_pipeline(info['best_model_key']).fit(train_data)
print(f'Stages: {[type(s).__name__ for s in loaded.stages]}')""")),
        md('## 3. Load Data Target'),
        code(t("csv_path = str(PROJECT_ROOT / '${P}')\nprint(f'Membaca: {csv_path}')\nudf = spark.read.option('header','true').option('multiLine','true').option('escape','\"').csv(csv_path)\nprint(f'Baris: {udf.count()}')", P=PATH_PREPROC)),
        md('## 4. Prediksi Label'),
        code("""for c in ('tokens',): 
    if c in udf.columns: udf = udf.drop(c)
udf = udf.withColumn(LABEL_COL, F.lit('dummy'))
pred = loaded.transform(udf).drop(LABEL_COL)
pred = map_prediction_labels(pred, loaded)
print('=== Distribusi Prediksi ===')
pred.groupBy('pred_label').count().orderBy('pred_label').show()
tp = pred.count()
for r in pred.groupBy('pred_label').count().orderBy('pred_label').collect():
    print(f'  {r["pred_label"]:10s}: {r["count"]:5d} ({r["count"]/tp*100:.1f}%)')
pred.select('comment_id', TEXT_COL, 'pred_label').show(5, truncate=60)"""),
        md('## 5. Simpan Hasil Auto-Labeling'),
        code(t("""al = pred.select('comment_id', TEXT_COL, F.col('pred_label').alias(LABEL_COL)).withColumn('_source', F.lit('auto_labeled'))
csv_path = str(OUTPUT_DIR / 'auto_labeled_data.csv')
al.toPandas().to_csv(csv_path, index=False, encoding='utf-8')
print(f'Auto-labeled: {csv_path}')
stats = {'model': info['best_model_display'], 'f1_macro': info['best_f1_macro'],
         'total': tp, 'dist': {str(r['pred_label']): int(r['count']) for r in pred.groupBy('pred_label').count().collect()},
         'timestamp': datetime.now(timezone.utc).isoformat()}
with open(str(OUTPUT_DIR / 'auto_labeling_stats.json'), 'w') as f: json.dump(stats, f, indent=2)
print(f'Stats saved.')""")),
        md('## 6. Stop Spark'),
        code("spark.stop()\nprint('Phase 2 selesai.')"),
    ])


# =============================================================
# Phase 3
# =============================================================
def make_phase3():
    return make_nb('# Phase 3: Train 2.000 Original, Test Auto-Labeled', [
        md('Train pada 2.000 original, test pada auto-labeled. Mengukur generalisasi ke data baru.'),
        md('## 1. Import & Inisialisasi'),
        code(t(UTILS_BLOCK, OUTPUT=OUTPUT_DIR, MODEL=MODEL_DIR)),
        code("spark = create_spark_session('phase3-2000-train-pseudo-test')\nspark.sparkContext.setLogLevel('WARN')\nprint(f'Spark: {spark.sparkContext.master}')"),
        md('## 2. Load Data'),
        code(t("""train_df = spark.read.option('header','true').option('multiLine','true').option('escape','"').csv(str(PROJECT_ROOT / '${SP}'))
test_df = spark.read.option('header','true').option('multiLine','true').option('escape','"').csv(str(PROJECT_ROOT / '${OP}' / 'auto_labeled_data.csv'))
print(f'Train: {train_df.count()}  |  Test: {test_df.count()}')
train_df.groupBy(LABEL_COL).count().orderBy(LABEL_COL).show()
test_df.groupBy(LABEL_COL).count().orderBy(LABEL_COL).show()""", SP=PATH_SENTIMENT, OP=OUTPUT_DIR)),
        md('## 3. Training'),
        code(t("""MODELS = [('logistic_regression','Logistic Regression'),('naive_bayes','Naive Bayes')]
results = {}
for mk, md_ in MODELS:
    t0 = time.time()
    results[md_] = train_and_evaluate(mk, md_, train_df, test_df)
    print(f'  Waktu: {time.time()-t0:.2f} dtk')""")),
        md('## 4. Evaluasi Lengkap'),
        code(EVAL_BLOCK),
        md('## 5. Simpan Hasil'),
        code(t("eval_path = str(OUTPUT_DIR / 'evaluation_phase3_2000_train_pseudo_test.json')\ncsv_prefix = 'predictions_phase3_2000_train_pseudo_test'\n" + SAVE_EVAL_BLOCK, OUTPUT=OUTPUT_DIR)),
        md('## 6. Stop Spark'),
        code("spark.stop()\nprint('Phase 3 selesai.')"),
    ])


# =============================================================
# Phase 4
# =============================================================
def make_phase4():
    return make_nb('# Phase 4: Seluruh Data (80/20)', [
        md('Gabung 2.000 original + auto-labeled, split 80/20 stratified. Latih LR + NB.'),
        md('## 1. Import & Inisialisasi'),
        code(t(UTILS_BLOCK, OUTPUT=OUTPUT_DIR, MODEL=MODEL_DIR)),
        code("spark = create_spark_session('phase4-all-80-20')\nspark.sparkContext.setLogLevel('WARN')\nprint(f'Spark: {spark.sparkContext.master}')"),
        md('## 2. Load & Gabung Data'),
        code(t("""dfo = spark.read.option('header','true').option('multiLine','true').option('escape','"').csv(str(PROJECT_ROOT / '${SP}'))
dfa = spark.read.option('header','true').option('multiLine','true').option('escape','"').csv(str(PROJECT_ROOT / '${OP}' / 'auto_labeled_data.csv'))
print(f'Original: {dfo.count()}  |  Auto-labeled: {dfa.count()}')
# Select common columns only, drop _source from auto-labeled
common_cols = [c for c in dfo.columns if c in dfa.columns]
df_all = dfo.select(*common_cols).unionByName(dfa.select(*common_cols)).cache()
print(f'Total: {df_all.count()}')
df_all.groupBy(LABEL_COL).count().orderBy(LABEL_COL).show()""", SP=PATH_SENTIMENT, OP=OUTPUT_DIR)),
        md('## 3. Stratified Split 80/20'),
        code("train_df, test_df = stratified_split(df_all)\nprint(f'Train: {train_df.count()}  |  Test: {test_df.count()}')"),
        md('## 4. Training'),
        code(t("""MODELS = [('logistic_regression','Logistic Regression'),('naive_bayes','Naive Bayes')]
results = {}
for mk, md_ in MODELS:
    t0 = time.time()
    results[md_] = train_and_evaluate(mk, md_, train_df, test_df)
    print(f'  Waktu: {time.time()-t0:.2f} dtk')""")),
        md('## 5. Evaluasi Lengkap'),
        code(EVAL_BLOCK),
        md('## 6. Simpan Hasil'),
        code(t("eval_path = str(OUTPUT_DIR / 'evaluation_phase4_all_80_20.json')\ncsv_prefix = 'predictions_phase4_all_80_20'\n" + SAVE_EVAL_BLOCK, OUTPUT=OUTPUT_DIR)),
        md('## 7. Ringkasan'),
        code("""print(f'Dataset: {df_all.count()} dokumen')
print(f'{"Model":<22} {"Accuracy":>10} {"F1-W":>10} {"F1-M":>10}')
print('-' * 56)
for name, res in results.items():
    m = res['test']
    print(f'{name:<22} {m["accuracy"]:>10.4f} {m["f1_weighted"]:>10.4f} {m["f1_macro"]:>10.4f}')"""),
        md('## 8. Stop Spark'),
        code("spark.stop()\nprint('Phase 4 selesai.')"),
    ])


# =============================================================
# Generate
# =============================================================
if __name__ == '__main__':
    for fname, nb_fn in [
        ('phase1_2000_80_20.ipynb', make_phase1),
        ('phase2_auto_labeling.ipynb', make_phase2),
        ('phase3_2000_train_pseudo_test.ipynb', make_phase3),
        ('phase4_all_80_20.ipynb', make_phase4),
    ]:
        NB_DIR.mkdir(parents=True, exist_ok=True)
        with open(str(NB_DIR / fname), 'w', encoding='utf-8') as f:
            nbf.write(nb_fn(), f)
        print(f'Created: {NB_DIR / fname}')
    print('\nDone.')
