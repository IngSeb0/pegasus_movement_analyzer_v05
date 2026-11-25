"""Descarga el catálogo y los FITS con la API de MontagePy 2.3.0."""
from ast import literal_eval
from hashlib import file_digest
from pathlib import Path
import json
import socket
import sys
from zipfile import ZipFile


def main():
    root=Path(__file__).resolve().parent
    runtime=root/'montagepy'
    with ZipFile(next(root.glob('montagepy-2.3.0-*.whl'))) as wheel:
        wheel.extractall(runtime)
    sys.path.insert(0,str(runtime))
    from MontagePy.archive import mArchiveList,mArchiveDownload
    socket.setdefaulttimeout(25)
    area=float(sys.argv[1])
    folder=root/('entradas-'+str(area))
    folder.mkdir()
    table=folder/'catalogo.tbl'
    raw=folder/'fits'
    records={}
    try:
        records['mArchiveList']=mArchiveList('2MASS J','M101',area,str(table))
        (folder/'DESCARGA.json').write_text(json.dumps(records,indent=2,default=str))
        assert table.is_file() and table.stat().st_size>0,'Catálogo ausente'
        downloaded=mArchiveDownload('2MASS J','M101',area,str(raw))
        records['mArchiveDownload']=literal_eval(downloaded) if isinstance(downloaded,str) else downloaded
        assert int(records['mArchiveDownload']['status'])==0,records
        inputs=[]
        for path in sorted(raw.glob('*.fits')):
            with path.open('rb') as stream:
                assert stream.read(8)==b'SIMPLE  ',path
                stream.seek(0)
                digest=file_digest(stream,'sha256').hexdigest()
            inputs.append(dict(archivo=path.name,bytes=path.stat().st_size,sha256=digest))
        assert inputs and len(inputs)==int(records['mArchiveDownload']['count'])
        (root/'ENTRADAS.json').write_text(json.dumps(dict(objeto='M101',banda='2MASS J',lado_grados=area,N=len(inputs),archivos=inputs),indent=2))
    except Exception as error:
        records['error']=repr(error)
        (folder/'DESCARGA.json').write_text(json.dumps(records,indent=2,default=str))
        raise


if __name__=='__main__':
    main()
