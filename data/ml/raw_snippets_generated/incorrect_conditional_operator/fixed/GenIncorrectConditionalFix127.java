public class GenIncorrectConditionalFix127 {
    static void printAll1(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static void printAll2(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static void printAll3(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static boolean isEven4(int steps) {
        return steps % 2 == 0;
    }

    static int largest5(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static String report(boolean loaded) {
        if (loaded == true) {
            return "active";
        }
        return "draft";
    }

    static void printAll6(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int average7(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
