# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from bokeh.io import output_notebook, output_file
from bokeh.layouts import layout, column, row
from bokeh.plotting import figure, show, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.models import CustomJS, MultiChoice, LabelSet, Div, Spinner, Button
from bokeh.models import PanTool, BoxZoomTool, BoxSelectTool, ResetTool, HoverTool
from bokeh.resources import INLINE

# %%
import pandas as pd
import numpy as np

# %%
import os
import sys
import argparse
import logging


# %%
def get_band(df_cnv, band_file):
    out_band = pd.DataFrame()
    df_band = pd.read_csv(band_file, sep='\t', header=None)
    df_band.columns=['chr', 'start', 'end', 'band']
    for c in df_cnv['chr'].unique():
        df_p = df_cnv.loc[df_cnv['chr']==c, :].copy()
        band_list = df_band.loc[df_band['chr']==c, 'band'].to_list()
        band_pos_list = df_band.loc[df_band['chr']==c, 'start'].to_list() + [np.inf]
        df_p['band'] = pd.cut(df_p['Position'], band_pos_list, labels=band_list)
        out_band = pd.concat([out_band, df_p])
    return out_band



# %% tags=[]
# output_notebook()
def get_plot(df, sampleName):
    for i in ['index', 'chr', 'Position', 'copyNum', 'band', 'color']:
        if i not in df.columns:
            loggiing.info(f'{sampleName} has not {i} column')
            return None

    TOOLTIPS = [
    #    ("index", "$index"),
    #    ("(x,y)", "($x, $y)"),
        ("Chr","@chr"),
        ("Position", "@Position"),
        ("band", "@band")
    ]

    div = Div(text='Chr infomation', style={'font-size':'large','ont-weight': 'bold'})
    p = figure(x_range=Range1d(0, df['index'].max()), 
               y_range=Range1d(0,5), 
               tooltips=TOOLTIPS,
               title = sampleName,
               tools = [PanTool(dimensions='width'), 
                        BoxZoomTool(dimensions='width'),
                        BoxSelectTool(dimensions='width'), 
                        ResetTool(), HoverTool()
                       ],
               aspect_ratio = 3,
               sizing_mode='stretch_width'
               # width=1200, height=400
              )

    list_pc = {}
    for c in df['chr'].unique():
        data1 = df.loc[df['chr']==c, :]
        data = ColumnDataSource(data1)
        pc = p.circle(x='index', y='copyNum', color='color', source=data, hover_color='red')
        list_pc[c] = {'chr':c, 'data':pc}
        data.selected.js_on_change('indices', CustomJS(args=dict(d=data,c=c.lstrip('chr'),div=div), 
                                                          code="""
                                                          const inds = d.selected.indices;
                                                          const data = d.data;
                                                          if (inds.length == 0){
                                                              return
                                                          }
                                                          var sum = 0
                                                          
                                                          //console.log(inds)
                                                          for(let i = 0; i < inds.length; i++) {
                                                              sum += data['copyNum'][inds[i]]
                                                              //console.log(data['Position'][inds[i]], data['copyNum'][inds[i]])
                                                          }
                                                          //console.log(inds.length)
                                                          //console.log(sum)
                                                          
                                                          var mean = (sum/inds.length).toFixed(2)
                                                          var first = inds[0]
                                                          var last = inds.at(-1)
                                                          //console.log(data['Position'][last] +"-"+ data['Position'][first])
                                                          var pos = ((data['Position'][last] - data['Position'][first])/1e6).toFixed(2)
                                                          var band = data['band'][first] +"-"+ data['band'][last]
                                                          div.text = "(" + c + ")(" + band + "," + pos +"Mb)(" + mean + ")"
                                                          """
                                                         )
        )

    source = ColumnDataSource(df.drop_duplicates(subset='chr', keep='first'))
    labels = LabelSet(x='index', y=4, text='chr', x_offset=5, y_offset=10, source=source)#render_mode='canvas')
    p.add_layout(labels)
    spinner = Spinner(title="Circle size",low=0.5,high=10,step=0.5,value=3,)#width=200,)
    spinner.js_on_change("value", CustomJS(args=dict(lpc=list_pc), 
                                           code="""
                                           for(var key in lpc){
                                               lpc[key]['data'].glyph.size = this.value
                                           }
                                           """
                                          )
                        )


    OPTIONS = list(df['chr'].unique())
    multi_chr = MultiChoice(options=OPTIONS)# width=p.width)
    multi_chr.js_on_change('value', CustomJS(args=dict(lpc=list_pc, plot=p, div=div), 
                                             code="""
                                             var min_idx = plot.x_range.end
                                             var max_idx = plot.x_range.start
                                             var mean_chr = []
                                             for(var key in lpc){

                                                 if(this.value.includes(key)){
                                                     const tmp_idx = lpc[key]['data']['data_source']['data']['index']
                                                     var tmp_min_idx = Math.min.apply(null, tmp_idx)
                                                     var tmp_max_idx = Math.max.apply(null, tmp_idx)

                                                     const tmp_copyNum = lpc[key]['data']['data_source']['data']['copyNum']
                                                     var len = tmp_copyNum.length
                                                     var sum = 0
                                                     for(var i=0; i<len; i++){
                                                         sum += tmp_copyNum[i]
                                                     }
                                                     var tmp_mean = (sum/len).toFixed(2)
                                                     mean_chr.push("("+key.replace('chr','')+")("+tmp_mean+")")

                                                     if(tmp_min_idx<min_idx){
                                                         min_idx = tmp_min_idx
                                                     }
                                                     if(tmp_max_idx>max_idx){
                                                         max_idx = tmp_max_idx
                                                     }
                                                     lpc[key]['data'].visible=true

                                                }else{
                                                    lpc[key]['data'].visible=false
                                                }
                                             }

                                             plot.x_range.start = min_idx
                                             plot.x_range.end = max_idx
                                             div.text = mean_chr.join("; ")
                                             """
                                            )
                          )
    
    all_present = Button(label='全部显示')
    all_absent = Button(label='全部清除')
    all_absent.js_on_click(CustomJS(args=dict(multi_chr=multi_chr),
                                    code="""
                                    multi_chr.value = []
                                    """
                                   )
                          )
    all_present.js_on_click(CustomJS(args=dict(multi_chr=multi_chr, s=source),
                                    code="""
                                    multi_chr.value = s.data['chr']
                                    """
                                   )
                          )
    p_out = column(row(spinner, all_absent, all_present), multi_chr, div, p)
    return p_out
# show()

# %% tags=[]
def get_data(cnv_file, band_file):
    df = pd.read_csv(cnv_file)
    df['chr_int'] = df['chr'].str.lstrip(r'Cchr').str.replace(r'[Yy]', '24', regex=True).str.replace(r'[Xx]', '23', regex=True).astype(int)
    df = df.sort_values(by=['chr_int', 'Position']).reset_index().drop('index',axis=1).reset_index()
    df['color'] = df['chr_int'].map(lambda x: 'red' if x%2 else 'blue')
    df = get_band(df, band_file)
    return df


# %% tags=[]
if __name__ == '__main__':
    bin_dir = os.path.split(os.path.realpath(__file__))[0]
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', nargs="+", default=None, help='input chromosome copy number csv[chr, Position, copyNum] sep by [,]')
    parser.add_argument('-id', '--inputdir', default=None, help='input dir for all csv file')
    parser.add_argument('-r', '--refband', default=os.path.join(bin_dir, 'hg19_band.txt'), help='human chromosome band [chr, start, end, band] sep by tab')
    parser.add_argument('-o', '--outputfile', default='cnv_check_js.html', help='output html file')
    parser.add_argument('-d', '--outputdir', default=None, help='output html dir for split')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    
    outdir = args.outputdir
    outfile = args.outputfile
    if not outdir and (not outfile):
        logging.info('outputfile or outputdir should be defined')
        sys.exit()
    
    if args.inputdir:
        inputdir = args.inputdir
        cnv_files = [os.path.join(inputdir, i) for i in os.listdir(inputdir) if os.path.splitext(i)[1]=='.csv']
    elif args.input:
        cnv_files = args.input
    else:
        logging.info('inputfile or inputdir should be defined')
        sys.exit()
    
    # cnv_file = 'test_input.csv'
    # band_file = 'hg19_band.txt'
    
    band_file = args.refband
    
    total_p = []
    sampleNames = []
    for cnv_file in cnv_files:
        df_cnv = get_data(cnv_file, band_file)
        sn = os.path.split(cnv_file)[1]
        p = get_plot(df_cnv, sampleName=sn)
        total_p.append(p)
        sampleNames.append(sn)
    
    if outdir:
        for p, sn in zip(total_p, sampleNames):
            output_file(os.path.join(outdir, sn+'_cnv_check_js.html'))
            save(p, title=sn)
    else:
        output_file(outfile)
        save(column(total_p), title='cnv_check_js', resources=INLINE)
