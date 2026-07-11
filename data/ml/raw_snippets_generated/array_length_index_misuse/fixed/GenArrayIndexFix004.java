public class GenArrayIndexFix004 {
    static void printAll1(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static void stampLast(int[] prices, int value) {
        prices[prices.length - 1] = value;
    }

    static boolean isEven2(int total) {
        return total % 2 == 0;
    }

    static String describe3(int budget) {
        if (budget < 10) {
            return "low";
        } else if (budget > 50) {
            return "high";
        }
        return "medium";
    }
}
