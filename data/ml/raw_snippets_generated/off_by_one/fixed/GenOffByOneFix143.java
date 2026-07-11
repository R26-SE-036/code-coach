public class GenOffByOneFix143 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describe2(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }

    static void printAll3(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static int sum4(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static void show(int[] sizes) {
        for (int i = 0; i < sizes.length; i++) {
            System.out.println(sizes[i]);
        }
    }
}
