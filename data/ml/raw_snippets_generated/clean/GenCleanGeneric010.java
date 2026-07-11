public class GenCleanGeneric010 {
    static void printAll1(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll3(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static boolean isEven4(int budget) {
        return budget % 2 == 0;
    }
}
