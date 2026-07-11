public class GenArrayIndexFix139 {
    static void printAll1(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int largest2(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static void showLast(int[] marks) {
        System.out.println(marks[marks.length - 1]);
    }

    static int sum3(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
