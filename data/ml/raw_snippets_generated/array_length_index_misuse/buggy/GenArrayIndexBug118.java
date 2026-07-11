public class GenArrayIndexBug118 {
    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static int lastOf(int[] stocks) {
        return stocks[stocks.length];
    }
}
