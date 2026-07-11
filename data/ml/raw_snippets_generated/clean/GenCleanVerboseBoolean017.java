public class GenCleanVerboseBoolean017 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String toggle(boolean verified) {
        if (verified == true) {
            return "on";
        }
        return "off";
    }

    static void printAll3(int[] scores) {
        for (int value : scores) {
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

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven6(int total) {
        return total % 2 == 0;
    }

    static void printAll7(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static boolean isEven8(int budget) {
        return budget % 2 == 0;
    }
}
