using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace fw_updater
{
    public partial class Form1 : Form
    {

        private string dfuUtilFirmware = "";
        private string firmwareFilename = "";

        object lockDfu = new object();

        private bool downloadAttempted = false;

        public Form1()
        {
            InitializeComponent();

            dfuUtilFirmware = ExtractFromAssembly("fw_updater.Resources.dfu_util.exe");
            firmwareFilename = ExtractFromAssembly("fw_updater.Resources.DiVA.dfu");

            DfuVersionCheck();

            /* Attempt cleanup, but it's not essential if these fail to remove. */
            try
            {
                if (File.Exists(dfuUtilFirmware)) File.Delete(dfuUtilFirmware);
                if (File.Exists(firmwareFilename)) File.Delete(firmwareFilename);
            }
            catch
            {

            }
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            /* Start off timer when window loaded */
            timer1_Tick(null, null);
        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            if (DfuDetectDiVA())
            {
                label1.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(0)))), ((int)(((byte)(192)))), ((int)(((byte)(0)))));
                label1.Text = "Device Detected";

                pictureBox1.Image = Properties.Resources._0858_checkmark_circle;
                label2.Text = "";

                button1.Enabled = true;
                progressBar1.Visible = false;

                /* reset flag */
                downloadAttempted = false;
            }
            else if (!downloadAttempted)
            {
                label1.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(0)))), ((int)(((byte)(0)))));
                label1.Text = "Device Not Detected";

                pictureBox1.Image = Properties.Resources._0859_cross_circle;
                label2.Text = "Please Connect Device while\r\nholding down upper button";
                button1.Enabled = false;
            }

            timer1.Interval = 500;
            timer1.Start();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            if (button1.Enabled)
            {
                timer1.Stop();
                button1.Enabled = false;
                pictureBox1.Image = Properties.Resources._0173_hdd_down;
                label1.Text = "Updating";
                progressBar1.Value = 0;
                progressBar1.Visible = true;

                downloadAttempted = true;

                /* Start the update */
                DfuUpdate();
            }

        }

        private void DfuVersionCheck()
        {
            lock (lockDfu)
            {
                var standardOutput = ExecuteProcess(dfuUtilFirmware, "--version");
                if (!standardOutput.Contains("dfu-util 0.9"))
                {
                    throw new ApplicationException("Error executing dfu-util");
                }
            }
        }

        private bool DfuDetectDiVA()
        {
            lock (lockDfu)
            {
                var standardOutput = ExecuteProcess(dfuUtilFirmware, "--list");
                return standardOutput.Contains("Found DFU: [16d0:0fad]");
            }
        }

        private void DfuUpdate()
        {
            lock (lockDfu)
            {
                Task.Run(() =>
                {
                    ExecuteProcessWithProgress(dfuUtilFirmware, "-D " + firmwareFilename);
                });
            }
        }

        private string ExecuteProcess(string command, string commandArguments)
        {
            string returnString = "";
            using (Process process = new Process())
            {
                process.StartInfo.Arguments = commandArguments;
                process.StartInfo.FileName = command;

                process.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
                process.StartInfo.CreateNoWindow = true;
                process.StartInfo.UseShellExecute = false;
                process.StartInfo.RedirectStandardOutput = true;
                process.Start();
                returnString = process.StandardOutput.ReadToEnd();
            }

            return returnString;
        }

        private void ExecuteProcessWithProgress(string command, string commandArguments)
        {
            string errorString = "";
            Process process = new Process();
            process.StartInfo.Arguments = commandArguments;
            process.StartInfo.FileName = command;


            process.StartInfo.WindowStyle = ProcessWindowStyle.Hidden;
            process.StartInfo.CreateNoWindow = true;
            process.StartInfo.UseShellExecute = false;
            process.StartInfo.RedirectStandardOutput = true;
            process.StartInfo.RedirectStandardError = true;
            process.OutputDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    /* Strings we are interested in has the following form:
                     *   `Download\t[===                      ]  14%        61440 bytes\r`
                     *   `Download done.\r\n`
                     *   We don't really need/care about the ascii progress bar as we can use a gui progressbar.
                     *   We can extract the decimal number used for percentage with a bit of regex.
                     */
                    if (e.Data.StartsWith("Download\t"))
                    {
                        var percentage = int.Parse(Regex.Match(e.Data, @"\d+").Groups[0].Value);
                        /* Update gui with this information */
                        Invoke(new MethodInvoker(() =>
                        {
                            label2.Text = string.Format("{0}%", percentage);
                            progressBar1.Value = percentage;
                        }));

                    }
                    if (e.Data.StartsWith("Download done."))
                    {
                        /* Update gui if we see that we're done */
                        Invoke(new MethodInvoker(() =>
                        {
                            label2.Text = "100%";
                            progressBar1.Value = 100;

                            label1.Text = "Complete";
                            pictureBox1.Image = Properties.Resources._0858_checkmark_circle;

                        }));
                    }
                }
            };

            process.ErrorDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    if (e.Data.Contains("Error"))
                    {
                        errorString = e.Data;

                        /* Update gui with error info */
                        Invoke(new MethodInvoker(() =>
                        {
                            label1.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(0)))), ((int)(((byte)(0)))));
                            label1.Text = "Error";

                            pictureBox1.Image = Properties.Resources._0853_notification;
                        }));
                    }

                }
            };
            process.Start();

            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            process.WaitForExit();

            Invoke(new MethodInvoker(() =>
            {
                /* Highlight error string if present */
                if (!string.IsNullOrEmpty(errorString))
                {
                    label2.Text = errorString;
                }

                /* Start timer to look for new devices */
                timer1_Tick(null, null);
            }));
        }

        private string ExtractFromAssembly(string resource_name)
        {
            string strPath = Path.GetTempFileName();
            if (File.Exists(strPath)) File.Delete(strPath);
            Assembly assembly = Assembly.GetExecutingAssembly();

            using (var input = assembly.GetManifestResourceStream(resource_name))
            using (var output = File.Open(strPath, FileMode.CreateNew))
            {
                CopyStream(input, output);
            }

            return strPath;
        }

        private void CopyStream(Stream input, Stream output)
        {
            byte[] buffer = new byte[32768];
            while (true)
            {
                int read = input.Read(buffer, 0, buffer.Length);
                if (read <= 0)
                    return;
                output.Write(buffer, 0, read);
            }
        }
    }
}
