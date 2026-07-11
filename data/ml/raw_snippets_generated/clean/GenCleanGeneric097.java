public class GenCleanGeneric097 {
    static String describe1(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
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

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
