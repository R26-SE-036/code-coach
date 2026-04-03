package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug007 {
    public static void main(String[] args) {
        int[] prices = { 100, 200, 300 };
        int total = 0;

        for (int i = 0; i <= prices.length; i++) {
            total += prices[i];
        }

        System.out.println(total);
    }
}