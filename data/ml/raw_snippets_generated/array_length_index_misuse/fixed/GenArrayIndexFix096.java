public class GenArrayIndexFix096 {
    static void printAll1(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static void stampLast(int[] scores, int value) {
        scores[scores.length - 1] = value;
    }

    static int sum2(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int drain3(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static String describe4(int count) {
        if (count < 100) {
            return "low";
        } else if (count > 500) {
            return "high";
        }
        return "medium";
    }

    static int sum5(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }
}
