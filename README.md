# CNVcheck



## 功能

基于bokeh将human染色体CNV文件生成交互网页，便于评估CNV



## 用法

- 单文件生成单页面

  ```shell
  python CNV_check_js.py -i test_input.csv -o test_out.html
  ```



- 多文件生成单页面

  ```shell
  python CNV_check_js.py -id /path/to/csv/dir/ -o test_out.html
  ```

  

- 多文件生成多页面

  ```shell
  python CNV_check_js.py -id /path/to/csv/dir/ -d /path/to/out/dir/
  ```

  