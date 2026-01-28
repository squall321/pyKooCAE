from waitress import serve
import KooAnalysisWeb

serve(KooAnalysisWeb.app, host='0.0.0.0',port=5000)
