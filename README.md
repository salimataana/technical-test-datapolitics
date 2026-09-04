# Technical Test – Datapolitics

## 1. Description

Ce projet implémente un moteur de recherche sémantique local permettant de rechercher des informations dans un ensemble de documents PDF.

L'application est composée de deux parties principales :

* une **pipeline d'ingestion** permettant de lire les PDF, d'extraire leur contenu, de les découper en morceaux (*chunks*) et de générer leurs embeddings ;
* une **API FastAPI** permettant d'effectuer une recherche sémantique dans les documents.

Le système fonctionne entièrement en local et n'utilise aucune API payante.

### Technologies principales

* Python 3.12
* PyMuPDF pour l'extraction de texte des PDF
* Tesseract OCR pour les PDF scannés
* Sentence-Transformers pour les embeddings
* FAISS pour la recherche vectorielle
* FastAPI pour l'API HTTP
* Docker pour reproduire l'environnement d'exécution
* Pytest pour les tests

---

## 2. Architecture

Le fonctionnement général est le suivant :

```text
                    INGESTION
                       │
                       ▼
                 Dossier de PDF
                       │
                       ▼
                 Extraction texte
                 ┌─────┴─────┐
                 │           │
             PDF texte    PDF scanné
                 │           │
             PyMuPDF     Tesseract OCR
                 │           │
                 └─────┬─────┘
                       ▼
                    Chunks
                       │
                       ▼
              Sentence-Transformers
                       │
                       ▼
                  Embeddings
                       │
                       ▼
                     FAISS
                       │
              ┌────────┴────────┐
              ▼                 ▼
        index.faiss       metadata.json


                     RECHERCHE
                         │
                         ▼
                  Question utilisateur
                         │
                         ▼
                    Embedding
                         │
                         ▼
                   Recherche FAISS
                         │
                         ▼
                   Meilleurs chunks
                         │
                         ▼
                   Métadonnées
                         │
                         ▼
                      JSON
```

L'index FAISS contient les vecteurs.

Le fichier `metadata.json` permet de retrouver les informations associées à chaque vecteur : document, page, chunk et texte.

---

## 3. Structure du projet

```text
technical-test-datapolitics/
│
├── data/
│   └── *.pdf
│
├── storage/
│   ├── index.faiss
│   └── metadata.json
│
├── src/
│   └── pdf_search/
│       ├── api/
│       │   └── main.py
│       │
│       ├── ingestion/
│       │   ├── cli.py
│       │   ├── extractor.py
│       │   ├── chunker.py
│       │   └── embedder.py
│       │
│       └── search/
│           └── faiss_store.py
│
├── tests/
│   ├── test_api.py
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_extractor.py
│   └── test_faiss_store.py
│
├── .gitignore
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 4. Installation locale

### Prérequis

* Python 3.12+
* Tesseract OCR
* Git

Créer et activer un environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installer le projet et ses dépendances :

```bash
pip install -e ".[dev]"
```

Pour l'OCR, Tesseract doit également être installé sur le système.

Sur Ubuntu :

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra
```

La langue française est nécessaire pour permettre à Tesseract de traiter correctement les documents en français.

---

## 5. Ajouter les documents PDF

Placer les documents PDF dans le dossier :

```text
data/
```

Par exemple :

```text
data/
├── document1.pdf
├── document2.pdf
└── document3.pdf
```

Le script d'ingestion parcourt automatiquement les fichiers ayant l'extension `.pdf`.

---

## 6. Lancer l'ingestion

L'ingestion se lance avec le chemin du dossier contenant les PDF :

```bash
python -m pdf_search.ingestion.cli data
```

Le script effectue les opérations suivantes :

1. recherche les fichiers PDF ;
2. extrait le texte page par page ;
3. utilise PyMuPDF pour les PDF contenant du texte ;
4. utilise Tesseract OCR lorsque le texte extrait est insuffisant ;
5. découpe le texte en chunks ;
6. génère un embedding pour chaque chunk ;
7. construit l'index FAISS ;
8. sauvegarde l'index et les métadonnées.

Les fichiers générés sont :

```text
storage/index.faiss
storage/metadata.json
```

### Exemple de statistiques

Avec le corpus utilisé pendant le développement :

```text
Nombre total de chunks : 207
Nombre total de pages : 64
Nombre de pages avec OCR : 2
Nombre de vecteurs dans FAISS : 207
```

Ces valeurs dépendent évidemment des documents présents dans `data/`.

---

## 7. Pourquoi utiliser des chunks ?

Un document PDF complet peut être trop long pour être représenté efficacement par un seul embedding.

Le texte est donc découpé en morceaux.

La configuration utilisée par défaut est :

* taille maximale : 1000 caractères ;
* chevauchement : 150 caractères.

Le chevauchement permet de conserver une partie du contexte entre deux chunks consécutifs.

Chaque chunk conserve également :

* le nom du document ;
* le numéro de page ;
* son index dans la page ;
* son texte.

---

## 8. Embeddings

Le modèle utilisé est :

```text
paraphrase-multilingual-MiniLM-L12-v2
```

Il est particulièrement adapté à ce projet car il prend en charge plusieurs langues, dont le français.

Le modèle est exécuté localement et ne nécessite pas d'API payante.

Chaque chunk est transformé en un vecteur de dimension 384.

La requête utilisateur est transformée avec le même modèle afin de pouvoir être comparée aux vecteurs des documents.

Les embeddings sont normalisés :

```python
normalize_embeddings=True
```

Cette normalisation permet d'utiliser la similarité cosinus avec FAISS via un produit scalaire (*inner product*).

---

## 9. Recherche vectorielle avec FAISS

FAISS est utilisé avec :

```python
'faiss.IndexFlatIP'
```

`IP` signifie *Inner Product*.

Les embeddings étant normalisés, le produit scalaire entre deux vecteurs correspond à leur similarité cosinus.

Le principe est donc :

```text
Question
   ↓
Embedding
   ↓
Comparaison avec les embeddings des chunks
   ↓
Scores de similarité
   ↓
Top K résultats
```

Pour chaque résultat, l'application récupère ensuite les métadonnées correspondant à l'identifiant du vecteur FAISS.

---

## 10. Lancer l'API

Une fois l'index créé :

```bash
uvicorn pdf_search.api.main:app --reload
```

L'API est alors disponible sur :

```text
http://127.0.0.1:8000
```

La documentation interactive Swagger est disponible sur :

```text
http://127.0.0.1:8000/docs
```

---

## 11. Endpoint `/search`

### Méthode

```text
POST /search
```

### Pourquoi POST ?

La recherche reçoit des données envoyées par le client, notamment :

* la question ;
* le nombre de résultats souhaités.

Le client envoie donc un objet JSON au serveur.

### Exemple de requête

```json
{
  "query": "Qui a signé la convention de mécénat ?",
  "top_k": 5
}
```

### Exemple de réponse

```json
{
  "query": "Qui a signé la convention de mécénat ?",
  "results": [
    {
      "document_name": "document.pdf",
      "page_number": 5,
      "chunk_index": 0,
      "extraction_method": "text",
      "score": 0.43,
      "text": "..."
    }
  ]
}
```

### Exemple avec curl

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Qui a signé la convention de mécénat ?",
    "top_k": 5
  }'
```

Chaque résultat contient :

* `document_name` : nom du PDF ;
* `page_number` : page du document ;
* `chunk_index` : position du chunk ;
* `extraction_method` : méthode utilisée, `text` ou `ocr` ;
* `score` : score de similarité ;
* `text` : contenu du chunk.

`top_k` est limité entre 1 et 20 afin d'éviter des requêtes excessives.

---

## 12. Tests

Les tests sont exécutés avec :

```bash
pytest
```

La suite actuelle couvre notamment :

* extraction de texte PDF ;
* extraction OCR ;
* découpage en chunks ;
* normalisation et dimension des embeddings ;
* création et recherche FAISS ;
* validation des paramètres de l'API.

Le nombre exact de tests peut évoluer. Le résultat est vérifié automatiquement par GitHub Actions à chaque push et pull request.

```bash
python -m pytest -q
```

### GitHub Actions

Le workflow `.github/workflows/ci.yml` se lance à chaque push et pull request. Il installe Python 3.12 et Tesseract avec la langue française, exécute les tests et vérifie la construction de l'image Docker.

---

## 13. Utilisation avec Docker

Docker permet de reproduire l'environnement nécessaire à l'application sans avoir à installer manuellement toutes les dépendances.

L'image contient notamment :

* Python 3.12 ;
* les dépendances Python du projet ;
* Tesseract OCR ;
* la langue française de Tesseract ;
* le code de l'application.

### Construire l'image

Depuis la racine du projet :

```bash
docker build -t pdf-search .
```

### Lancer l'application

```bash
docker run --rm -p 8000:8000 \
  -v "$(pwd)/storage:/app/storage" \
  pdf-search
```

Le modèle Sentence-Transformers est téléchargé lors du premier démarrage si son cache n'est pas déjà disponible. Avec `docker run --rm`, ce cache n'est pas conservé entre deux conteneurs.

L'API est ensuite disponible sur :

```text
http://127.0.0.1:8000
```

Swagger :

```text
http://127.0.0.1:8000/docs
```

### Pourquoi monter `storage/` ?

Le volume :

```bash
-v "$(pwd)/storage:/app/storage"
```

permet au conteneur d'utiliser les fichiers persistants du projet :

```text
storage/index.faiss
storage/metadata.json
```

Ainsi, les données générées ne sont pas perdues lorsque le conteneur est supprimé.

---

## 14. Ingestion avec Docker

Pour reconstruire l'index avec les PDF présents dans `data/`, l'ingestion peut également être exécutée dans le conteneur.

Par exemple :

```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/storage:/app/storage" \
  pdf-search \
  python -m pdf_search.ingestion.cli data
```

Cette commande monte :

* `data/` dans le conteneur pour fournir les PDF ;
* `storage/` pour conserver l'index et les métadonnées.

Après modification ou ajout de PDF, il faut relancer l'ingestion afin de reconstruire l'index.

---

## 15. Que faire lorsque les PDF changent ?

L'index FAISS est construit à partir des documents présents au moment de l'ingestion.

Si des PDF sont ajoutés, supprimés ou modifiés :

1. placer les nouveaux PDF dans `data/` ;
2. relancer l'ingestion ;
3. le fichier `storage/index.faiss` est recréé ;
4. le fichier `storage/metadata.json` est recréé ;
5. redémarrer l'API si nécessaire.

L'approche retenue est volontairement simple et adaptée à un petit corpus.

---

## 16. Gestion des PDF scannés

Certains PDF ne contiennent pas de texte exploitable directement.

Pour ces documents, PyMuPDF peut retourner très peu de texte.

Dans ce cas, l'application utilise automatiquement Tesseract OCR.

Le fonctionnement est :

```text
PDF
 ↓
Extraction PyMuPDF
 ↓
Texte insuffisant ?
 ├── Non → texte conservé
 └── Oui → page convertie en image
             ↓
          Tesseract OCR
             ↓
           texte
```

La méthode utilisée est également conservée dans les données d'ingestion sous la forme :

```text
text
```

ou :

```text
ocr
```

Cela permet notamment de suivre combien de pages ont nécessité de l'OCR.

---

## 17. Limites connues

### Recherche sémantique

La recherche utilise une similarité vectorielle et ne garantit pas que le chunk contenant la réponse exacte soit toujours classé premier.

Par exemple, une question sur les signataires d'une convention peut faire remonter en premier des passages parlant de la convention et de sa signature, même si les noms des signataires apparaissent dans un chunk légèrement moins bien classé.

Cela constitue une limite normale d'une recherche sémantique basée uniquement sur les embeddings.

### Découpage

Le découpage actuel est basé sur le nombre de caractères.

Il peut donc couper :

* une phrase ;
* un mot ;
* un paragraphe.

Une amélioration possible serait d'utiliser un découpage basé sur les paragraphes ou les phrases, tout en conservant une limite de taille.

### OCR

L'OCR est plus lent que l'extraction directe de texte et peut produire des erreurs sur :

* les tableaux ;
* les documents de mauvaise qualité ;
* certaines polices ;
* les mises en page complexes.

### Mise à jour de l'index

L'index est actuellement reconstruit lorsqu'une nouvelle ingestion est effectuée.

Il n'y a pas encore de système d'indexation incrémentale permettant de ne recalculer que les documents modifiés.

### Taille du corpus

`IndexFlatIP` effectue une comparaison avec les vecteurs du corpus.

Cette solution est simple et adaptée à un petit corpus, mais elle serait moins adaptée à plusieurs millions de documents.

---

## 18. Choix techniques

### Pourquoi FAISS ?

FAISS est une bibliothèque spécialisée dans la recherche de vecteurs.

Elle est simple à utiliser et adaptée à un petit corpus local.

Elle permet également de sauvegarder l'index sur disque.

### Pourquoi un modèle local ?

Le test demande une solution sans API payante.

Le modèle Sentence-Transformers est donc exécuté localement.

Cela évite d'envoyer le contenu des documents à un service externe.

### Pourquoi FastAPI ?

FastAPI permet de créer rapidement une API HTTP typée avec validation automatique des données grâce à Pydantic.

Il fournit également automatiquement une documentation Swagger.

### Pourquoi Docker ?

Docker permet de reproduire l'environnement nécessaire au fonctionnement de l'application, notamment :

* Python ;
* les dépendances Python ;
* Tesseract ;
* la langue française de Tesseract.

---

## 19. Améliorations possibles

Pour une version de production, plusieurs améliorations pourraient être envisagées :

* découpage des textes basé sur les phrases et paragraphes ;
* recherche hybride combinant recherche lexicale et recherche sémantique ;
* reranking des résultats ;
* index FAISS approximatif pour les très gros volumes ;
* indexation incrémentale ;
* configuration des paramètres via variables d'environnement ;
* traitement par batch configurable pour les embeddings ;
* monitoring et logs structurés ;
* authentification et contrôle d'accès ;
* stockage des documents et métadonnées dans une base de données ;
* déploiement de l'API derrière un reverse proxy ;
* workers multiples pour la production.

---

## 20. Architecture de production envisagée

Pour un environnement de production avec un volume important, l'architecture pourrait évoluer vers :

```text
                    Utilisateur
                         │
                         ▼
                  API / Reverse Proxy
                         │
                         ▼
                    FastAPI
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Service de recherche   Service d'ingestion
              │                     │
              ▼                     ▼
         Index vectoriel       Stockage documents
              │
              ▼
       Base de métadonnées
```

La version actuelle reste volontairement simple afin de répondre au besoin du test technique avec un petit corpus local.

---

## 21. Résumé

Le projet fournit un moteur de recherche sémantique local capable de :

* lire des documents PDF ;
* gérer les PDF textuels et scannés ;
* effectuer de l'OCR en français ;
* découper les documents en chunks ;
* générer des embeddings localement ;
* indexer ces embeddings avec FAISS ;
* conserver les métadonnées des chunks ;
* exposer une API FastAPI ;
* effectuer des recherches sémantiques via `POST /search` ;
* fonctionner dans un conteneur Docker.

Le système privilégie une architecture simple, locale et reproductible, adaptée au périmètre du test technique.
