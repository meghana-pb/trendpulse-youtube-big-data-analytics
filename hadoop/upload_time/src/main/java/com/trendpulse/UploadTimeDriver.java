package com.trendpulse;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

/** TrendPulse - Upload Time Analysis Driver */
public class UploadTimeDriver {
    public static void main(String[] args) throws Exception {
        if(args.length<2){System.err.println("Usage: UploadTimeDriver <input> <output>");System.exit(1);}
        Configuration conf=new Configuration();
        Job job=Job.getInstance(conf,"TrendPulse-UploadTimeAnalysis");
        job.setJarByClass(UploadTimeDriver.class);
        job.setMapperClass(UploadTimeMapper.class);
        job.setReducerClass(UploadTimeReducer.class);
        job.setOutputKeyClass(Text.class); job.setOutputValueClass(Text.class);
        job.setNumReduceTasks(1);
        FileInputFormat.addInputPath(job,new Path(args[0]));
        FileOutputFormat.setOutputPath(job,new Path(args[1]));
        System.out.println("[TrendPulse] Upload Time Analysis job submitted.");
        System.exit(job.waitForCompletion(true)?0:1);
    }
}
