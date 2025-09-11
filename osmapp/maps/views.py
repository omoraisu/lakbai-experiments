from django.shortcuts import render
from django.http import JsonResponse
from .utils import get_edges_gdf

def show_map(request):
    return render(request, "maps/old_map.html")


def street_geojson(request):
    gdf = get_edges_gdf()
    return JsonResponse(gdf.to_json(), safe=False)
