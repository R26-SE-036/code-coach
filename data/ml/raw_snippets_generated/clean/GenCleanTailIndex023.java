public class GenCleanTailIndex023 {
    static void printAll1(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static int sum2(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static int tail(int[] values) {
        return values[values.length - 1];
    }
}
