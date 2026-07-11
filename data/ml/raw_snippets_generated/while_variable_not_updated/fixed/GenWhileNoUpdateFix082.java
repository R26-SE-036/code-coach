public class GenWhileNoUpdateFix082 {
    static void countdown(int count) {
        while (count > 0) {
            System.out.println("left: " + count);
            count--;
        }
    }

    static void printAll1(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }
}
