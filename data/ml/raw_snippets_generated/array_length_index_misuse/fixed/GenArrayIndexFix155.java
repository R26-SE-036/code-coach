public class GenArrayIndexFix155 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll2(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int lastOf(int[] prices) {
        return prices[prices.length - 1];
    }
}
