"""
    Copyright 2021 Dugal Harris - dugalh@gmail.com

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import collections
import json
import os
import pathlib

import click
import ee
from collections import namedtuple

from geedim import export as export_api
from geedim import collection as coll_api
from geedim import info, image

# map collection names to classes
# from geedim.collection import cls_from_coll


class _CmdChainResults(object):
    def __init__(self):
        self.search_ids = None
        self.search_region = None
        self.comp_image = None
        self.comp_id = None

def _extract_region(region=None, bbox=None, region_buf=5):
    """ create geojson dict from region or bbox """

    if (bbox is None or len(bbox)==0) and (region is None):
        raise click.BadOptionUsage('Either pass --region or --bbox', region)

    if isinstance(region, dict):
        region_geojson = region
    elif region is not None:  # read region file/string
        region = pathlib.Path(region)
        if 'json' in region.suffix:  # read region from geojson file
            with open(region) as f:
                region_geojson = json.load(f)
        else:  # read region from raster file
            try:
                region_geojson, _ = image.get_image_bounds(region, region_buf)
            except Exception as ex:
                raise click.BadParameter(f'{region} is not a valid geojson or raster file. \n{ex}')
    else:  # convert bbox to geojson
        xmin, ymin, xmax, ymax = bbox
        coordinates = [[xmax, ymax], [xmax, ymin], [xmin, ymin], [xmin, ymax], [xmax, ymax]]
        region_geojson = dict(type='Polygon', coordinates=[coordinates])

    return region_geojson

def _export_im_list(im_list, path='', wait=True, overwrite=False, download=True, **kwargs):

    click.echo('\nDownloading:\n') if download else click.echo('\nExporting:\n')
    export_tasks = []

    for im_dict in im_list:
        if download:
            filename = pathlib.Path(path).joinpath(im_dict['name'] + '.tif')
            export_api.download_image(im_dict['image'], filename, overwrite=overwrite, **kwargs)
        else:
            task = export_api.export_image(im_dict['image'], im_dict['name'], folder=path, wait=False, **kwargs)
            export_tasks.append(task)

    if wait:
        for task in export_tasks:
            export_api.monitor_export_task(task)

def _create_im_list(ids, **kwargs):
    im_list = []

    for im_id in ids:
        ee_coll_name, im_idx = image.split_id(im_id)
        if not ee_coll_name in info.ee_to_gd:
            im_list.append(dict(image=ee.Image(im_id), name=im_id.replace('/','-')))
        else:
            gd_image = image.get_class(ee_coll_name).from_id(im_id, **kwargs)
            im_list.append(dict(image=gd_image, name=im_id.replace('/','-')))

    return im_list

def _export_download(res=_CmdChainResults(), download=True, **kwargs):

    # unpack arguments into a named tuple
    arg_tuple = namedtuple('arg_tuple', kwargs)
    params = arg_tuple(**kwargs)

    if (params.region is None) and (params.bbox is None or len(params.bbox)==0):
        if res.search_region is None:
            raise click.BadOptionUsage('Either pass --region / --box, or chain this command with `search`', params.region)
        else:
            region = res.search_region
    else:
        region = _extract_region(region=params.region, bbox=params.bbox)

    im_list=[]
    if res.comp_image is not None:
        im_list.append(dict(image=res.comp_image, name=res.comp_id.replace('/', '-')))
    elif res.search_ids is not None:
        im_list = _create_im_list(res.search_ids, mask=params.mask, scale_refl=params.scale_refl)
    elif len(params.id) > 0:
        im_list = _create_im_list(params.id, mask=params.mask, scale_refl=params.scale_refl)
    else:
        raise click.BadOptionUsage('Either pass --id, or chain this command with `search` or `composite`', id)

    if download:
        _export_im_list(im_list, region=region, path=params.download_dir, crs=params.crs, scale=params.scale,
                        overwrite=params.overwrite, download=True)
    else:
        _export_im_list(im_list, region=region, path=params.drive_folder, crs=params.crs, scale=params.scale,
                        download=False)


# define options common to >1 command
bbox_option = click.option(
    "-b",
    "--bbox",
    type=click.FLOAT,
    nargs=4,
    help="Region defined by bounding box co-ordinates in WGS84 (xmin, ymin, xmax, ymax).  "
         "[One of --bbox or --region is required.]",
    required=False,
    default=None
)
region_option = click.option(
    "-r",
    "--region",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True,
                    allow_dash=False),
    help="Region defined by geojson or raster file.  [One of --bbox or --region is required.]",
    required=False
)
region_buf_option = click.option(
    "-rb",
    "--region_buf",
    type=click.FLOAT,
    default=5,
    help="If --region is a raster file, extend the region bounds by region_buf %",
    required=False,
    show_default=True
)
image_id_option = click.option(
    "-i",
    "--id",
    type=click.STRING,
    help="Earth engine image ID(s).",
    required=False,
    multiple=True
)
crs_option = click.option(
    "-c",
    "--crs",
    type=click.STRING,
    default=None,
    help="Reproject image(s) to this CRS (WKT or EPSG string). \n[default: source CRS]",
    required=False
)
scale_option = click.option(
    "-s",
    "--scale",
    type=click.FLOAT,
    default=None,
    help="Resample image bands to this pixel resolution (m). \n[default: minimum of the source band resolutions]",
    required=False
)
mask_option = click.option(
    "-m/-nm",
    "--mask/--no-mask",
    default=False,
    help="Do/don't apply (cloud and shadow) nodata mask(s).  [default: no-mask]",
    required=False,
)
scale_refl_option = click.option(
    "-sr/-nsr",
    "--scale-refl/--no-scale-refl",
    default=True,
    help="Scale reflectance bands from 0-10000.  [default: scale-refl]",
    required=False,
)
add_aux_option = click.option(
    "-aa/-naa",
    "--add-aux/--no-add-aux",
    default=True,
    help="Add auxiliary bands (masks and quality score) to the image .  [default: add-aux]",
    required=False,
)


# define the click cli
@click.group(chain=True)
@click.pass_context
def cli(ctx):
    ee.Initialize()
    ctx.obj = _CmdChainResults()


@click.command()
@click.option(
    "-c",
    "--collection",
    type=click.Choice(list(info.gd_to_ee.keys()), case_sensitive=False),
    help="Earth Engine image collection to search.",
    default="landsat8_c2_l2",
    required=True
)
@click.option(
    "-s",
    "--start-date",
    type=click.DateTime(),
    help="Start date (UTC).",
    required=True
)
@click.option(
    "-e",
    "--end-date",
    type=click.DateTime(),
    help="End date (UTC).  \n[default: start_date + 1 day]",
    required=False,
)
@bbox_option
@region_option
@click.option(
    "-vp",
    "--valid-portion",
    type=click.FloatRange(min=0, max=100),
    default=0,
    help="Lower limit of the portion of valid (cloud and shadow free) pixels (%).",
    required=False
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=False, resolve_path=True,
                    allow_dash=False),
    default=None,
    help="Write results to this filename, file type inferred from extension: [.csv|.json]",
    required=False
)
@region_buf_option
@click.pass_obj
def search(res, collection, start_date, end_date=None, bbox=None, region=None, valid_portion=0, output=None, region_buf=5):
    """ Search for images """

    res.search_region = _extract_region(region=region, bbox=bbox, region_buf=region_buf)

    click.echo(f'\nSearching for {info.gd_to_ee[collection]} images between '
               f'{start_date.strftime("%Y-%m-%d")} and {end_date.strftime("%Y-%m-%d")}...')

    gd_collection = coll_api.Collection(collection)
    im_df = gd_collection.search(start_date, end_date, res.search_region, valid_portion=valid_portion)
    res.search_ids = im_df.ID.values.tolist()

    if len(res.search_ids) == 0:
        click.echo('No images found\n')
    else:
        click.echo(f'{len(res.search_ids)} images found\n')
        click.echo(f'Image property descriptions:\n\n{gd_collection.summary_key}\n')
        click.echo(f'Search Results:\n\n{gd_collection.summary}')

    if (output is not None):
        output = pathlib.Path(output)
        if output.suffix == '.csv':
            im_df.to_csv(output, index=False)
        elif output.suffix == '.json':
            im_df.to_json(output, orient='index')
        else:
            raise ValueError(f'Unknown output file extension: {output.suffix}')
    return


cli.add_command(search)


@click.command()
@image_id_option
@bbox_option
@region_option
@click.option(
    "-dd",
    "--download-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, readable=False, resolve_path=True,
                    allow_dash=False),
    default=os.getcwd(),
    help="Download image file(s) to this directory",
    required=False,
    show_default=True
)
@crs_option
@scale_option
@mask_option
@scale_refl_option
@click.option(
    "-o",
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the destination file if it exists.  [default: prompt the user for confirmation]",
    required=False,
    show_default=False
)
@click.pass_context
def download(ctx, id=[], bbox=None, region=None, download_dir=os.getcwd(), crs=None, scale=None, mask=False, scale_refl=True,
             overwrite=False):
    """ Download image(s), with cloud and shadow masking """
    _export_download(res=ctx.obj, download=True, **ctx.params)

cli.add_command(download)


@click.command()
@image_id_option
@bbox_option
@region_option
@click.option(
    "-df",
    "--drive-folder",
    type=click.STRING,
    default='',
    help="Export image(s) to this Google Drive folder. [default: root]",
    required=False,
)
@crs_option
@scale_option
@mask_option
@scale_refl_option
@click.option(
    "-w/-nw",
    "--wait/--no-wait",
    default=True,
    help="Wait / don't wait for export to complete.  [default: wait]",
    required=False,
)
@click.pass_context
def export(ctx, id=[], bbox=None, region=None, drive_folder='', crs=None, scale=None, mask=False, scale_refl=True,
           wait=True):
    """ Export image(s) to Google Drive, with cloud and shadow masking """
    _export_download(res=ctx.obj, download=False, **ctx.params)

cli.add_command(export)

@click.command()
@image_id_option
@click.option(
    "-cm",
    "--method",
    type=click.Choice(coll_api.Collection._composite_methods, case_sensitive=False),
    help="Compositing method to use.",
    default="q_mosaic",
    show_default = True,
    required=False
)
@click.option(
    "-m/-nm",
    "--mask/--no-mask",
    default=True,
    help="Do/don't apply (cloud and shadow) nodata mask(s) before compositing.  [default: mask]",
    required=False,
)
@scale_refl_option
@click.pass_obj
def composite(res, id=None, mask=True, scale_refl=False, method='q_mosaic'):
    """ Create a cloud-free composite image """

    id = list(id)
    if (id is None or len(id) == 0):
        if res.search_ids is None:
            raise click.BadOptionUsage('Either pass --id, or chain this command with `search`', id)
        else:
            id = res.search_ids
            res.search_ids = None

    gd_collection = coll_api.Collection.from_ids(id, mask=mask, scale_refl=scale_refl)

    res.comp_image, res.comp_id = gd_collection.composite(method=method)

cli.add_command(composite)

##
