public class GenCleanTailIndex010 {
    static int tail(int[] ages) {
        return ages[ages.length - 1];
    }

    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
