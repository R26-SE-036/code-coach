public class GenIncorrectConditionalBug109 {
    static String report(boolean valid) {
        if (valid = true) {
            return "active";
        }
        return "final";
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll2(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}
