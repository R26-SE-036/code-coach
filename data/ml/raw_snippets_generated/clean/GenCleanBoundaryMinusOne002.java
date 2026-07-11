public class GenCleanBoundaryMinusOne002 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }

    static String describe3(int steps) {
        if (steps < 100) {
            return "low";
        } else if (steps > 500) {
            return "high";
        }
        return "medium";
    }

    static String describe4(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static int tally(int[] marks) {
        int total = 0;
        for (int i = 0; i <= marks.length - 1; i++) {
            total += marks[i];
        }
        return total;
    }

    static void printAll5(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static void printAll6(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int sum7(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }
}
