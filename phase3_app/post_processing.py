"""Reviewed transformations from the team's notebooks, adapted for one-person uploads."""
import re
import numpy as np
import pandas as pd
from collections import Counter

def prepare_posts(raw):
    df=raw.rename(columns={'patient_id':'patient'}).copy()
    df['date']=pd.to_datetime(df['date'],format='mixed',errors='raise')
    df=df.drop_duplicates(['patient','date','text'])
    if len(df)<5:raise ValueError('Please include at least five distinct posts.')
    EMOJI_RE = re.compile('[🌀-\U0001faff☀-➿🇦-🇿\u200d️]+')
    df['emoji_count'] = df['text'].str.count(EMOJI_RE.pattern)
    df['text'] = df['text'].str.replace(EMOJI_RE, ' ', regex=True)
    before = {'links': df['text'].str.contains('https?://\\S+|www\\.\\S+', regex=True, na=False).sum(), 'emails': df['text'].str.contains('\\S+@\\S+\\.\\S+', regex=True, na=False).sum(), 'mentions': df['text'].str.contains('@\\w+', regex=True, na=False).sum(), 'phones': df['text'].str.contains('\\+?\\d[\\d\\s\\-]{7,}\\d', regex=True, na=False).sum()}
    df['text'] = df['text'].str.replace('https?://\\S+|www\\.\\S+', ' ', regex=True).str.replace('\\S+@\\S+\\.\\S+', ' [EMAIL] ', regex=True).str.replace('@\\w+', ' [PERSON] ', regex=True).str.replace('\\+?\\d[\\d\\s\\-]{7,}\\d', ' [PHONE] ', regex=True).str.replace('\\d{6,}', ' [ID] ', regex=True)
    after = {'links': df['text'].str.contains('https?://\\S+|www\\.\\S+', regex=True, na=False).sum(), 'emails': df['text'].str.contains('\\S+@\\S+\\.\\S+', regex=True, na=False).sum(), 'mentions': df['text'].str.contains('@\\w+', regex=True, na=False).sum(), 'phones': df['text'].str.contains('\\+?\\d[\\d\\s\\-]{7,}\\d', regex=True, na=False).sum()}
    for k in before:
        pass
    ELONG_RE = re.compile('(.)\\1{2,}')
    df['elongation_count'] = df['text'].str.count(ELONG_RE.pattern)
    df['text'] = df['text'].str.replace(ELONG_RE, '\\1\\1', regex=True)
    TASHKEEL = '[\\u0610-\\u061A\\u064B-\\u065F\\u0670\\u06D6-\\u06ED]'
    ARABIC_NORMALIZE = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه', 'ؤ': 'و', 'ئ': 'ي'}
    before_tashkeel = df['text'].str.contains(TASHKEEL, regex=True, na=False).sum()
    df['text'] = df['text'].str.replace(TASHKEEL, '', regex=True).str.replace('ـ', '', regex=False)
    for a, b in ARABIC_NORMALIZE.items():
        df['text'] = df['text'].str.replace(a, b, regex=False)
    ids_in_text = df['text'].str.contains('\\bP\\d{3}\\b', regex=True, na=False).sum()
    df['text'] = df['text'].str.replace('\\bP\\d{3}\\b', ' [SELF] ', regex=True).str.replace('،', ',', regex=False).str.replace('؛', ';', regex=False).str.replace('؟', '?', regex=False).str.replace('\\s+', ' ', regex=True).str.strip()
    no_tags = df['text'].str.replace('\\[(EMAIL|PERSON|PHONE|ID|SELF)\\]', ' ', regex=True)
    has_en = no_tags.str.contains('[A-Za-z]{2,}', regex=True, na=False)
    mostly_en = no_tags.str.count('[A-Za-z]') > no_tags.str.count('[\\u0600-\\u06FF]')
    df['mostly_english'] = mostly_en.astype(int)
    df['text'] = df['text'].str.replace('[A-Za-z]+', lambda m: m.group(0).lower(), regex=True)
    df['text'] = df['text'].str.replace('\\[(email|person|phone|id|self)\\]', lambda m: m.group(0).upper(), regex=True)
    DIAG_RE = '(?<!\\w)(?:ال)?(?:زهايمر|خرف)(?!\\w)|alzheimer\\w*|dementia'
    has_diag = df['text'].str.contains(DIAG_RE, regex=True, na=False)
    before = len(df)
    df = df[~has_diag]
    no_tags = df['text'].str.replace('\\[(EMAIL|PERSON|PHONE|ID|SELF)\\]', ' ', regex=True)
    df['n_words'] = no_tags.str.count('[\\u0600-\\u06FFa-z]{2,}')
    before = len(df)
    df = df[df['n_words'] > 0]
    TITLES = '(?:الاستاذ|استاذ|الاستاذه|الشيخ|شيخ|الدكتور|دكتور|الدكتوره|د\\s*/|د\\.|الحاج|الحاجه|المهندس|م\\s*/|ابو|ام)'
    NAME_AFTER_TITLE = f'(?<!\\w){TITLES}\\s+[\\u0600-\\u06FF]+(?:\\s+[\\u0600-\\u06FF]+)?'
    before_titles = df['text'].str.contains(NAME_AFTER_TITLE, regex=True, na=False).sum()
    df['text'] = df['text'].str.replace(NAME_AFTER_TITLE, ' [PERSON] ', regex=True)
    df['text'] = df['text'].str.replace('…\\s*more|\\.\\.\\.\\s*more|\\bmore\\b$', ' ', regex=True).str.replace('\\s+', ' ', regex=True).str.strip()
    TITLES = '(?:الاستاذ|استاذ|الاستاذه|الشيخ|شيخ|الدكتور|دكتور|الدكتوره|د\\s*/|د\\.|الحاج|الحاجه|المهندس|م\\s*/)'
    NAME_AFTER_TITLE = f'(?<!\\w){TITLES}\\s+[\\u0600-\\u06FF]+(?:\\s+[\\u0600-\\u06FF]+)?'
    before_titles = df['text'].str.contains(NAME_AFTER_TITLE, regex=True, na=False).sum()
    df['text'] = df['text'].str.replace(NAME_AFTER_TITLE, ' [PERSON] ', regex=True)
    df['text'] = df['text'].str.replace('…\\s*more|\\.\\.\\.\\s*more|\\bmore\\b$', ' ', regex=True).str.replace('\\s+', ' ', regex=True).str.strip()
    COPIED_RE = 'رواه|صلي الله عليه وسلم|قال تعالي|قال الله|سبحانه وتعالي|منقول|#|\\*[^*]{20,}\\*|\\"[^\\"]{40,}\\"|«[^»]{40,}»'
    df['copied'] = (df['text'].str.contains(COPIED_RE, regex=True, na=False) | (df['n_words'] > 120)).astype(int)
    own = df[df['copied'] == 0].groupby('patient').size()
    if len(df)<5:raise ValueError("Fewer than five usable posts remain after cleaning.")
    if not (df.copied==0).any():raise ValueError("Please include posts written in your own words.")
    return df

def extract_features(posts):
    df=posts.copy()
    df["label"]=0
    df["group"]="Not recorded"
    df["moca"]=np.nan
    df["split"]="submission"
    TAG_RE = re.compile('\\[(EMAIL|PERSON|PHONE|ID|SELF)\\]')
    WORD_RE = re.compile('[\\u0600-\\u06FFa-z]+')
    SENT_RE = re.compile('[.!?;,\\n]+')
    PRONOUNS = {'انا', 'انت', 'انتي', 'هو', 'هي', 'احنا', 'نحن', 'انتو', 'انتم', 'هم', 'هما', 'ده', 'دي', 'دا', 'دول', 'هذا', 'هذه', 'ذلك', 'تلك', 'اللي', 'الي', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    FILLERS = {'حاجه', 'حاجات', 'شي', 'شيء', 'كده', 'كدا', 'يعني', 'بقي', 'اهو', 'ايه', 'مش', 'عارف', 'عارفه', 'thing', 'stuff'}
    df['text'] = df['text'].fillna('').astype(str)
    own = df[df['copied'] == 0].copy()
    own['tokens'] = [WORD_RE.findall(TAG_RE.sub(' ', t)) for t in own['text']]
    own['n_tok'] = own['tokens'].str.len()
    own = own[own['n_tok'] > 0]
    def repeated_bigrams(tokens):
        bigrams = list(zip(tokens, tokens[1:]))
        return len(bigrams) - len(set(bigrams)) if bigrams else 0
    own['avg_word_len'] = [np.mean([len(w) for w in t]) for t in own['tokens']]
    own['n_sent'] = [max(1, len([s for s in SENT_RE.split(x) if s.strip()])) for x in own['text']]
    own['words_per_sent'] = own['n_tok'] / own['n_sent']
    own['n_pron'] = [sum((w in PRONOUNS for w in t)) for t in own['tokens']]
    own['n_fill'] = [sum((w in FILLERS for w in t)) for t in own['tokens']]
    own['n_rep_bigrams'] = [repeated_bigrams(t) for t in own['tokens']]
    own['n_bigrams'] = (own['n_tok'] - 1).clip(lower=0)
    from collections import Counter

    def mattr(tokens, w=50):
        if len(tokens) < w:
            return len(set(tokens)) / max(len(tokens), 1)
        c = Counter(tokens[:w])
        vals = [len(c) / w]
        for i in range(w, len(tokens)):
            out_t = tokens[i - w]
            c[out_t] -= 1
            if c[out_t] == 0:
                del c[out_t]
            c[tokens[i]] += 1
            vals.append(len(c) / w)
        return float(np.mean(vals))

    def hapax_ratio(tokens, w=100):
        chunks = [tokens[i:i + w] for i in range(0, len(tokens) - w + 1, w)] or [tokens]
        return float(np.mean([sum((v == 1 for v in Counter(ch).values())) / len(ch) for ch in chunks]))
    own = own.sort_values(['patient', 'date'])
    rows = []
    for pid, g in own.groupby('patient'):
        toks = [w for t in g['tokens'] for w in t]
        rows.append({'patient': pid, 'own_posts': len(g), 'avg_words_per_post': g['n_tok'].mean(), 'avg_word_length': g['avg_word_len'].mean(), 'avg_sentence_length': g['n_tok'].sum() / g['n_sent'].sum(), 'mattr': mattr(toks), 'hapax_ratio': hapax_ratio(toks), 'pronoun_ratio': g['n_pron'].sum() / g['n_tok'].sum(), 'filler_ratio': g['n_fill'].sum() / g['n_tok'].sum(), 'repetition_rate': g['n_rep_bigrams'].sum() / max(g['n_bigrams'].sum(), 1)})
    writing = pd.DataFrame(rows)
    beh = df.groupby('patient').agg(n_posts=('text', 'size'), first_date=('date', 'min'), last_date=('date', 'max'), night_post_ratio=('date', lambda d: d.dt.hour.between(0, 4).mean()), emoji_per_post=('emoji_count', 'mean'), elongation_per_post=('elongation_count', 'mean'), english_share=('mostly_english', 'mean'), copied_share=('copied', 'mean'), label=('label', 'first'), group=('group', 'first'), moca=('moca', 'first'), split=('split', 'first')).reset_index()
    beh['active_months'] = ((beh['last_date'] - beh['first_date']).dt.days / 30.44).clip(lower=1)
    beh['posts_per_month'] = beh['n_posts'] / beh['active_months']
    features = writing.merge(beh.drop(columns=['first_date', 'last_date']), on='patient')
    features.drop(columns=['patient', 'group', 'split']).describe().round(3).T
    def part_stats(g):
        toks = [w for t in g['tokens'] for w in t]
        return {'mattr': mattr(toks), 'avg_words_per_post': g['n_tok'].mean(), 'avg_sentence_length': g['n_tok'].sum() / g['n_sent'].sum(), 'pronoun_ratio': g['n_pron'].sum() / g['n_tok'].sum(), 'filler_ratio': g['n_fill'].sum() / g['n_tok'].sum(), 'repetition_rate': g['n_rep_bigrams'].sum() / max(g['n_bigrams'].sum(), 1)}
    MIN_PER_HALF = 5
    change_rows = []
    for pid, g in own.groupby('patient'):
        g = g.sort_values('date')
        half = len(g) // 2
        row = {'patient': pid}
        if half >= MIN_PER_HALF:
            early, late = (part_stats(g.iloc[:half]), part_stats(g.iloc[half:]))
            for k in early:
                row[f'{k}_change'] = late[k] - early[k]
        change_rows.append(row)
    change = pd.DataFrame(change_rows)
    features = features.merge(change, on='patient', how='left')
    change_cols = [c for c in features.columns if c.endswith('_change')]
    features[change_cols] = features[change_cols].fillna(0)
    for key in ['mattr','avg_words_per_post','avg_sentence_length','pronoun_ratio','filler_ratio','repetition_rate']:
        if key+'_change' not in features:features[key+'_change']=0.0
    return features
