package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix013 {
    public double getLastPrice(double[] prices) {
        return prices[prices.length - 1];
    }
}
