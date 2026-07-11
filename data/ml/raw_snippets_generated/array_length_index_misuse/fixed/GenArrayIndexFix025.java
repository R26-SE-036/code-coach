public class GenArrayIndexFix025 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void showLast(int[] sizes) {
        System.out.println(sizes[sizes.length - 1]);
    }

    static void printAll2(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static void printAll3(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }
}
