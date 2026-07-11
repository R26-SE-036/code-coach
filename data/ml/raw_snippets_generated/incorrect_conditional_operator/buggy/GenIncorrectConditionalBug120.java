public class GenIncorrectConditionalBug120 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static void announce(int level) {
        if (level = 10) {
            System.out.println("hit the target");
        }
    }
}
