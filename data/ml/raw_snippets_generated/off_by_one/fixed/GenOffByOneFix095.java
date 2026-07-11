public class GenOffByOneFix095 {
    static void printAll1(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static void printAll2(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int[] duplicate(int[] totals) {
        int[] copy = new int[totals.length];
        for (int i = 0; i < totals.length; i++) {
            copy[i] = totals[i];
        }
        return copy;
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int sum6(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}
