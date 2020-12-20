""" Module for parsing FMS timings """

import tarfile as tf
import io
import pandas as pd
from gfdlvitals.util import gmeantools


__all__ = ["timing"]


def timing(ascii_file, fyear, outdir, label):
    """Extracts FMS timings

    Parameters
    ----------
    ascii_file : str, path-like
        Path to ascii tar file
    fyear : str
        Year to process (YYYY)
    outdir : str
        Path for output SQLite file
    label : str
        Name of output SQLite file
    """

    def ascii_tar_to_stats_df(ascii_file):
        """Subroutine to read fms.out from ascii tar file,
        extract the clock timings, and return a pandas dataframe

        Parameters
        ----------
        ascii_file : str, path-like
            Path to ascii tar file

        Returns
        -------
        pandas.DataFrame of timings
        """

        member = None
        tar = tf.open(ascii_file)
        for member in tar.getnames():
            if "fms.out" in member:
                break

        txtfile = tar.extractfile(member)
        content = txtfile.readlines()
        x = -1
        for x, line in enumerate(content):
            if "Total runtime" in line.decode("utf-8"):
                break
        tar.close()
        content = content[x::]

        output = io.BytesIO()
        output.write(str.encode("clock,min,max,mean,std\n"))
        for line in content:
            line = line.decode("utf-8")
            if not line.startswith(" "):
                line = line.split()
                line = line[-1::-1]
                label = " ".join(line[8::][-1::-1])
                label = label.replace(" ", "_")
                label = label.replace("-", "_")
                label = label.replace("&", "_")
                for x in ["(", ")", "*", "/", ":"]:
                    label = label.replace(x, "")
                line = [label] + line[0:8][-1::-1][0:4]
                line = ",".join(line) + "\n"
                output.write(str.encode(line))
        output.seek(0)

        df = pd.read_csv(output, delimiter=",")
        # df = df.set_index('clock')

        return df

    df = ascii_tar_to_stats_df(ascii_file)

    clocks = sorted(df["clock"].to_list())
    for clock in clocks:
        for attr in ["mean", "min", "max"]:
            val = df[df["clock"] == clock][attr].values[0]

            # -- Write to sqlite
            gmeantools.write_sqlite_data(
                outdir + "/" + fyear + ".globalAve" + label + ".db",
                clock + "_" + attr,
                fyear[:4],
                val,
            )
