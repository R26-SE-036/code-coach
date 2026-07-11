public class GenWhileNoUpdateBug029 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void countdown(int count) {
        while (count > 0) {
            System.out.println("left: " + count);
        }
    }
}
