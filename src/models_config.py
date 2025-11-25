import os

ROOT_PATH=os.path.dirname(os.getcwd())

MODELS_PATH_BY_NAME = {#模型名称转地址
    'wreckage' : r'',
    'person' : r'',
    'tree' : r'',
    'floating' : rf'{ROOT_PATH}\models\floating_detect_v2.pt',
    'gate' : r'',
}

MODELS_LABELS_BY_NAME = {#模型需要检测类型
    'wreckage' : [],
    'person' : [],
    'tree' : [],
    'floating' : [0,1,2,3,4,5,6,7], #['ball', 'bottle', 'branch', 'grass', 'leaf', 'milk-box', 'plastic-bag', 'plastic-garbage']
    'gate' : [],
}
