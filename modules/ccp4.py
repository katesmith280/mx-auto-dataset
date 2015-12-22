from .base import Base
import subprocess
import os

from custom_parser import get_summary

class Process(Base):
    def process(self, **kwargs):
        super(Process, self).process(**kwargs)
        
        self.dataset.status = self.__class__.__name__
        self.dataset.save()

    def __write_logfile(self, process, output):
        logfile = os.path.join(self.project_dir, "%s.log" % process)
        with open(logfile, 'w') as f:
            f.write(output)


    def run_process(self, input_, args):
        process = subprocess.Popen(args,
                                   stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE,
                                    stdin=subprocess.PIPE,
                                    cwd=self.project_dir)
        out, err = process.communicate(input='\n'.join(input_))

        self.__write_logfile(args[0], out)

class Pointless(Process):
    def __init__(self, run_name, *args, **kwargs):
        super(Pointless, self).__init__()
        self.run_name = run_name

    def process(self, **kwargs):
        super(Pointless, self).process(**kwargs)
        
        #xdsin = os.path.basename(getattr(self, 'xds_%s' % self.run_name))
        xdsin = 'XDS_ASCII.HKL_%s' % self.run_name
        hklout = 'pointless_%s.mtz' % self.run_name

        args = ['pointless', 'XDSIN', xdsin, 'HKLOUT', hklout]
        stdin = []
        self.run_process(stdin, args)
        
class Aimless(Process):
    def __init__(self, run_name, *args, **kwargs):
        super(Aimless, self).__init__()
        self.run_name = run_name

    def process(self, **kwargs):
        super(Aimless, self).process(**kwargs)
        
        hklin = 'pointless_%s.mtz' % self.run_name
        hklout = 'aimless_%s.mtz' % self.run_name

        args = ['aimless', 'HKLIN', hklin, 'HKLOUT', hklout]
        stdin = ["run 1 all",
                "cycles 20",
                "anomalous on",
                "sdcorrection 1.3 0.02",
                "reject 4", ""]
        self.run_process(stdin, args)
        self.harvest()

    def harvest(self):
        logfile = os.path.join(self.project_dir, 'aimless.log')
        summary = get_summary(logfile)

        space_group = ''.join(summary['space_group'])
        unit_cell=summary['average_unit_cell']
        average_mosaicity=summary['average_mosaicity'][0]
        del summary['space_group'], summary['average_unit_cell'], summary['average_mosaicity']

        self.dataset.__dict__.update(space_group=space_group,
                     resolution=summary['high_resolution_limit'][0],
                     unit_cell=unit_cell,
                     average_mosaicity=average_mosaicity,
                     #status='Success',
                     #success=True,
                     #completed=True,
                     #processing_dir=self.project_dir,
                     **summary)
        self.dataset.save()        

class Truncate(Process):
    def __init__(self, run_name, *args, **kwargs):
        super(Truncate, self).__init__()
        self.run_name = run_name

    def process(self, **kwargs):
        super(Truncate, self).process(**kwargs)
        
        hklin = 'aimless_%s.mtz' % self.run_name
        hklout = 'truncate_%s.mtz' % self.run_name

        args =  ['truncate', 'HKLIN', hklin, 'HKLOUT', hklout]
        stdin = ["anomalous yes",
                "nresidue 1049",
                "labout  F=FP SIGF=SIGFP DANO=DANO_sulf SIGDANO=SIGDANO_sulf", ""]

        self.run_process(stdin, args)