public class GenArrayIndexBug031 {
    static int lastOf(int[] stocks) {
        return stocks[stocks.length];
    }

    static int sum1(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }
}
