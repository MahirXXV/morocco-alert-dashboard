# Morocco Alert Dashboard 🇲🇦

Cette application agrège les alertes publiques (manifestations, météo, sécurité) pour le Maroc et les affiche avec filtrage par gravité, carte interactive, statistiques, et notifications Telegram.

## Fonctionnalités
- Agrégation multi-sources (RSS marocains et internationaux)
- Filtrage par mots-clés et gravité
- Carte interactive (Folium)
- Notifications Telegram automatiques pour alertes graves
- Tableau de bord et statistiques en temps réel

## Déploiement

### Option 1 : Render.com (recommandé)
1. Crée un compte sur https://render.com
2. Connecte ton GitHub avec ce dépôt
3. Render détectera automatiquement `render.yaml` et lancera l'app

### Option 2 : Local (test)
```bash
pip install -r requirements.txt
streamlit run app.py
```
