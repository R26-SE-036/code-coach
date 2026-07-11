public class GenIncorrectConditionalBug002 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static boolean matches(boolean loaded, boolean armed) {
        if (loaded = armed) {
            return true;
        }
        return false;
    }

    static void printAll2(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
