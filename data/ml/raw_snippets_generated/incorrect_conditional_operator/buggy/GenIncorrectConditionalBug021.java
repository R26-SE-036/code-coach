public class GenIncorrectConditionalBug021 {
    static boolean isEven1(int quota) {
        return quota % 2 == 0;
    }

    static void printAll2(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static boolean matches(boolean armed, boolean active) {
        if (armed = active) {
            return true;
        }
        return false;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void printAll4(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
