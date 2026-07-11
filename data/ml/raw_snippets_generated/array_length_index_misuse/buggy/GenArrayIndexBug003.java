public class GenArrayIndexBug003 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void showLast(int[] stocks) {
        System.out.println(stocks[stocks.length]);
    }
}
