# APR-Framework

##### 디버깅 프로세스 통합 자동화 프레임워크란?

> **FL(Fault Localization)** + **APR(Automated Program Repair)** + **RT(Regression Testing)** 를 통합한 자동화 프레임워크로 버기 프로그램에 대한 패치를 자동으로 생성

### Setup

#### Install OS packages

```
sudo apt-get install python3 python3-pip
```

#### Set Python enviroment & packages

```
source env/bin/activate
```

or

```
pip install -r requirements.txt
```

#### Running APR-Framework

```
python run.py -p 1
```

### Command line arguments

- `-p` flag specifies the number of project(1~17)
- `-t` flag specifies the timeout for **RT** of Testcases
- `-g` flag specifies the number of patch generation per buggy in **APR**
- `-s` flag specifies the number of random seed

## Contributor
- Dongwook Choi (dwchoi95@skku.edu)
- Jinyoung Kim (danpoong@g.skku.edu)
- Jinseok Heo (mrhjs225@skku.edu)
- Youngkyung Kim (agnes66@skku.edu)
- Hohyeon Jeong (jeonghh89@skku.edu)
- Misoo Kim (misoo.kim@jnu.ac.kr)
- Eunseok Lee (leees@skku.edu)

## Acknowledgements
This work was supported by the National Research Foundation of Korea(NRF) grant funded by the Korea government(MSIT) (No. 2019R1A2C2006411). 