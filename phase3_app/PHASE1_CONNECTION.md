# Phase 1 connection

See START_HERE_AR.txt for installation, file paths and scope. All 23 exported features are kept separate from patient/group/MoCA/split/label metadata. Train/test IDs, split labels and reference labels in the supplied exports were checked for consistency. There are 209 unique patients, 167 training rows and 42 test rows, with no overlap and no missing CSV cells.

No raw post texts were supplied. Monthly posting charts and upstream cleaning funnels remain unavailable. Early/late change fields represent differences between two halves of the patient's own-post history, not a monthly prediction timeline. When fewer than 10 own-word posts exist, zero-filled change fields are marked insufficient history.

Only Senior and Clinician were connected to Phase 1. Researcher retains the evaluation template with explicit placeholder labels; About & Privacy retains its template. No model training, inference, probability or risk threshold was added.

Local original exports are included in data/phase1 and excluded from Git. The separate test_patients.csv is a reference list; the application reads features_test.csv for test-patient features. Uploaded exports live only in the Streamlit session. Offline HTML deliberately contains placeholders only.
