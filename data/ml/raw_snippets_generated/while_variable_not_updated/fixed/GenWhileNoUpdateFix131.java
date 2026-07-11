public class GenWhileNoUpdateFix131 {
    static void countdown(int count) {
        while (count > 0) {
            System.out.println("left: " + count);
            count--;
        }
    }
}
