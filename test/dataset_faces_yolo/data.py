import yaml

data = {
    'path': '/home/elisa/uni/tfg-ematos/test/dataset_faces_yolo/dataset',  
    'train': 'images/train-pro',  
    'val': 'images/val-pro', 
    'test': 'images/test-pro',
    'names': {
        0: 'Adri',
        1: 'Elisa',
        2: 'Will'
    }
}

with open('../dataset_faces_yolo/data.yaml', 'w') as file:
    yaml.dump(data, file, 
              default_flow_style=False, 
              sort_keys=False)
