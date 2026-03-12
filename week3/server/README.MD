# Week 3 - Simple MCP Server with TMDB API

## Isi proyek
- `server/main.py` -> semua kode server MCP
- `server/requirements.txt` -> dependency

## Fitur
Server ini punya 2 tool:
1. `search_movies(query, year=None)`
2. `get_movie_details(movie_id)`

## API yang dipakai
TMDB API:
- `GET /search/movie`
- `GET /movie/{movie_id}`

## Cara jalanin

```bash
cd week3_simple/server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TMDB_API_KEY="ISI_TOKEN_TMDB_KAMU"
python main.py
```

## Contoh konfigurasi Claude Desktop

```json
{
  "mcpServers": {
    "tmdb-simple": {
      "command": "python",
      "args": ["/absolute/path/to/week3_simple/server/main.py"],
      "env": {
        "TMDB_API_KEY": "ISI_TOKEN_TMDB_KAMU"
      }
    }
  }
}
```

## Alur kerja kode
1. User memanggil tool dari client MCP
2. Server menerima parameter
3. Server validasi input sederhana
4. Server memanggil TMDB API
5. Hasil dikembalikan dalam bentuk JSON sederhana
