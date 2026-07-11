public class GenOffByOneFix147 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int largest3(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static void printAll5(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static void show(int[] values) {
        for (int i = 0; i < values.length; i++) {
            System.out.println(values[i]);
        }
    }

    static void printAll6(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static String join7(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll8(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }
}
