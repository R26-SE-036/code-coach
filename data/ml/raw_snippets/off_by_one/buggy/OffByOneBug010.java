package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug010 {
    public static void main(String[] args) {
        int[] temps = { 30, 32, 35, 31 };
        int max = temps[0];

        for (int i = 0; i <= temps.length; i++) {
            if (temps[i] > max) {
                max = temps[i];
            }
        }

        System.out.println(max);
    }
}