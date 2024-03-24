gdal_merge.py -o rgbnir.tif -of GTiff -separate B04.tif B03.tif B02.tif B08.tif
gdal_translate -of COG rgbnir.tif rgbnir_cog.tif
```