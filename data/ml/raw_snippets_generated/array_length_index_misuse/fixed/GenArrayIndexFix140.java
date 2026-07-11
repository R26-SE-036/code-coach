public class GenArrayIndexFix140 {
    static boolean isEven1(int limit) {
        return limit % 2 == 0;
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static void printAll3(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static void showLast(int[] sizes) {
        System.out.println(sizes[sizes.length - 1]);
    }
}
