'''
Created on 2018年4月13日
# os.system(command)
# os.popen
# commands.getoutput(cmd), commands.getstatus, commands.getstatusoutput
@author: ythu
'''
from configparser import ConfigParser
import os
import shutil
import tarfile
import paramiko
import time

CONFIG_PATH = "xjd_pack.conf";

SECTION_LOCAL = "local"
SECTION_TARGET = "target"
SECTION_SFTP = "sftp"
SECTION_LINUX = "linux"


class Pack():
    
    def __init__(self):
        # 属性
        self.conf = ConfigParser()
        self.__init_conf()
        
        # 属性
        self.local = dict()
        try:
            self.__init_local()
        except(Exception) as e:
            print('初始化异常：%s' % e)
            return
        
        # 属性
        self.target = dict()
        try:
            self.__init_target()
        except(Exception) as e:
            print('初始化异常：%s' % e)
            return
        
        # 属性
        self.sftp = dict()
        try:
            self.__init_sftp()
        except(Exception) as e:
            print('初始化异常：%s' % e)
            return
        
        # 属性
        self.linux = dict()
        try:
            self.__init_linux()
        except(Exception) as e:
            print('初始化异常：%s' % e)
            return
    
    # 私有方法
    def __init_conf(self):
        """
        初始化配置文件
        """
        self.conf.read(CONFIG_PATH, "UTF-8")
    
    # 私有方法
    def __init_local(self):
        """
        初始化local section
        """
        print('初始化local section...开始')
        
        self.local['workspace_path'] = self.conf.get(SECTION_LOCAL, "workspace-path")  # 工作空间目录
        self.local['project_name'] = self.conf.get(SECTION_LOCAL, "project-name")  # 项目名称
        self.local['pack_module_names'] = self.conf.get(SECTION_LOCAL, "pack-module-names").split(",")  # 打包的模块集合
        self.local['pack_module_versions'] = self.conf.get(SECTION_LOCAL, "pack-module-versions").split(",")  # 打包的模块版本集合
        self.local['pack_target_path'] = self.conf.get(SECTION_LOCAL, "pack-target-path")  # 打包后的目录
        
        if len(self.local.get('pack_module_names')) != len(self.local.get('pack_module_versions')):
            raise RuntimeError('模块名称和版本不对应，请核对查看...')
        
        print('初始化local section...完成')
    
    # 私有方法
    def __init_target(self):
        """
        初始化target section
        """
        print('初始化target section...开始')
        if len(self.local) < 1:
            raise RuntimeError('请先执行__init_local__方法初始化local section...')
        
        self.target['spring_profiles_actives_olds'] = self.conf.get(SECTION_TARGET, 'spring-profiles-actives-olds').split(",")
        self.target['spring_profiles_actives_news'] = self.conf.get(SECTION_TARGET, 'spring-profiles-actives-news').split(",")
        self.target['log4j2_root_olds'] = self.conf.get(SECTION_TARGET, 'log4j2-root-olds').split(",")
        self.target['log4j2_root_news'] = self.conf.get(SECTION_TARGET, 'log4j2-root-news').split(",")
        
        len_module = len(self.local.get('pack_module_names'))
        if len_module != len(self.target.get('spring_profiles_actives_olds')) or len_module != len(self.target.get('spring_profiles_actives_news')) or len_module != len(self.target.get('log4j2_root_olds')) or len_module != len(self.target.get('log4j2_root_news')):
            raise RuntimeError('目标配置与模块不对应，请核对查看...')
        
        print('初始化target section...完成')
    
    # 私有方法
    def __init_sftp(self):
        """
        初始化sftp配置
        """
        print("初始化sftp section...开始")
        
        self.sftp['sftp_hostname'] = self.conf.get(SECTION_SFTP, 'sftp-hostname')
        self.sftp['sftp_port'] = self.conf.get(SECTION_SFTP, 'sftp-port')
        self.sftp['sftp_name'] = self.conf.get(SECTION_SFTP, 'sftp-name')
        self.sftp['sftp_password'] = self.conf.get(SECTION_SFTP, 'sftp-password')
        
        print("初始化sftp section...结束")
    
    # 私有方法
    def __init_linux(self):
        """
        初始化linux配置
        """
        print("初始化linux section...开始")
        
        self.linux['linux_project_dir'] = self.conf.get(SECTION_LINUX, 'linux-project-dir').split(",")
        self.linux['linux_tomcat_startup'] = self.conf.get(SECTION_LINUX, 'linux-tomcat-startup').split(",")
        self.linux['linux_tomcat_shutdown'] = self.conf.get(SECTION_LINUX, 'linux-tomcat-shutdown').split(",")
        
        len_module = len(self.local.get('pack_module_names'))
        if len_module != len(self.linux.get('linux_project_dir')) or len_module != len(self.linux.get('linux_tomcat_startup')) or len_module != len(self.linux.get('linux_tomcat_shutdown')):
            raise RuntimeError('服务器路径配置与模块不对应，请核对查看...')
        
        print("初始化linux section...开始")
    
    # 方法
    def mvn_pack(self):
        """
        编译项目
        """
        print('执行编译项目...开始')
        project_pom_path = os.path.abspath(os.path.join(os.path.join(self.local.get("workspace_path"), self.local.get("project_name")), "pom.xml"))
        # mvn clean package -Dmaven.test.skip=true -fD:\tools\sts-3.9.1\workspace\parent\pom.xml
        # mvn -version
        cmd_call = '%s %s' % ('mvn clean package -Dmaven.test.skip=true', "-f" + project_pom_path)
        print('执行命令：%s' % cmd_call)
        try:
            os.system(cmd_call)
        except(Exception) as e:
            print('执行编译项目异常：%s' % e)
            return
        print('执行编译项目...结束')
    
    # 方法 
    def tar_pack(self):
        """
        压缩编译后的项目
        """
        print("压缩文件...开始")
        project_path = os.path.join(os.path.join(self.local.get("workspace_path"), self.local.get("project_name")))
        names = self.local.get("pack_module_names")
        versions = self.local.get("pack_module_versions")
        modules = [];
        for i in range(len(names)):
            modules.append(os.path.abspath(os.path.join(project_path, names[i], self.local.get('pack_target_path'), '%s-%s' % (names[i], versions[i]))))
        i = 0
        for module in modules:
            tar_filepath = module + os.sep + "WEB-INF.tar.gz"
            if os.path.exists(tar_filepath):
                os.remove(tar_filepath)
            tar = tarfile.open(tar_filepath, 'w:gz')
            # 文件夹路径, 文件夹名字, 文件名
            for dirpath, dirnames, filenames in os.walk(os.path.abspath(os.path.join(module, "WEB-INF"))):
                dirpath_ = os.path.relpath(dirpath, os.path.abspath(module))
                print(dirpath_)
                for filename in filenames:
                    fullpath = os.path.join(dirpath, filename)
                    
                    # 对web.xml和log4j2.xml进行特殊处理
                    dst1 = os.path.join(dirpath, filename + ".tmp")
                    if filename == "web.xml":
                        self.__edit_file(fullpath, dst1, self.target.get('spring_profiles_actives_olds')[i], self.target.get('spring_profiles_actives_news')[i])
                    if filename == "log4j2.xml":
                        self.__edit_file(fullpath, dst1, self.target.get('log4j2_root_olds')[i], self.target.get('log4j2_root_news')[i])
                    
                    # 添加压缩条码
                    tar.add(fullpath, arcname=os.path.join(dirpath_, filename))
                    
                    # 对web.xml和log4j2.xml进行特殊处理
                    if filename == "web.xml" or filename == "log4j2.xml":
                        self.__restore_file(dst1, fullpath)        
            i = i + 1
        print("压缩文件...结束")    
        
    # 私有方法
    def __edit_file(self, src, dst, old_content, new_content):
        """
        编辑文件，并生成了临时文件
        """
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, dst)
        file_data = ""
        with open(src, "r", encoding="utf-8") as f:
            for line in f:
                if old_content in line:
                    line = line.replace(old_content, new_content)
                file_data += line
        with open(src, "w", encoding="utf-8") as f:
            f.write(file_data)
    
    # 私有方法
    def __restore_file(self, src, dst):
        """
        还原文件，并删除临时文件
        """
        os.remove(dst)
        shutil.move(src, dst)
    
    # 方法
    def upload_file(self):
        print("上传文件...开始")
        try:
            # 上传文件
            transport = paramiko.Transport((self.sftp.get('sftp_hostname'), int(self.sftp.get('sftp_port'))))
            transport.connect(username=self.sftp.get('sftp_name'), password=self.sftp.get('sftp_password'))
            sftp = paramiko.SFTPClient.from_transport(transport);
            
            project_path = os.path.join(os.path.join(self.local.get("workspace_path"), self.local.get("project_name")))
            names = self.local.get("pack_module_names")
            versions = self.local.get("pack_module_versions")
            modules = [];
            for i in range(len(names)):
                modules.append(os.path.abspath(os.path.join(project_path, names[i], self.local.get('pack_target_path'), '%s-%s' % (names[i], versions[i]), "WEB-INF.tar.gz")))
            i = 0
            for module in modules:
                print("%s->%s%s" % (module, self.linux.get('linux_project_dir')[i], os.path.basename(module)))
                sftp.put(module, "%s%s" % (self.linux.get('linux_project_dir')[i], os.path.basename(module)))
                i = i + 1
            transport.close()
            
            # 创建SSH对象
            ssh = paramiko.SSHClient()
            # 允许连接不在know_hosts文件中的主机
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 连接服务器
            ssh.connect(hostname=self.sftp.get('sftp_hostname'), port=int(self.sftp.get('sftp_port')), username=self.sftp.get('sftp_name'), password=self.sftp.get('sftp_password'))
            # 执行命令
            i = 0
            for module in modules:
                print('%s' % module)
                command = 'tar -xzvf %s%s -C %s' % (self.linux.get('linux_project_dir')[i], os.path.basename(module), self.linux.get('linux_project_dir')[i]);
                print(command)
                stdin, stdout, stderr = ssh.exec_command(command)
                result = str(stdout.read(), "utf-8")
                print("进入并且解压文件：%s" % result)
                
                stdin, stdout, stderr = ssh.exec_command(self.linux.get('linux_tomcat_shutdown')[i])
                result = str(stdout.read(), "utf-8")
                print("关闭服务器：%s" % result)
                
                # 休息2s
                time.sleep(2)
                
                stdin, stdout, stderr = ssh.exec_command(self.linux.get('linux_tomcat_startup')[i])
                result = str(stdout.read(), "utf-8")
                print("启动服务器：%s" % result)
                
                i = i + 1
            # 关闭连接
            ssh.close()
        except(Exception) as e:
            print("上传文件异常：%s" % e)
            return
        print("上传文件...结束")


if __name__ == '__main__':
    print("脚本开始...")
    try:
        p = Pack();
        p.mvn_pack()
        p.tar_pack()
        p.upload_file()
    except(Exception) as e:
        print("脚本异常：%s" % e)
    print("脚本结束...")
