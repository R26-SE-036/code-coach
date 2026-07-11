public class GenCleanTailIndex029 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static int tail(int[] marks) {
        return marks[marks.length - 1];
    }
}
