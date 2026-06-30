package petclinic.views;

import io.micronaut.context.annotation.Prototype;
import io.micronaut.context.python.PythonContextRuntime;
import io.micronaut.core.io.Writable;
import io.micronaut.views.ViewsRenderer;
import org.graalvm.polyglot.Value;

import static io.micronaut.context.python.GraalPyRuntimeUtil.PYTHON;

@Prototype
public class PythonTemplateViewsRenderer implements ViewsRenderer<Object, Object> {
    private final Value renderView;
    private final Value exists;

    public PythonTemplateViewsRenderer() {
        this.renderView = PythonContextRuntime.getContext()
                .eval(PYTHON, "from petclinic.views.renderer import render_view\nrender_view");
        this.exists = PythonContextRuntime.getContext()
                .eval(PYTHON, "from petclinic.views.renderer import exists\nexists");
    }

    @Override
    public Writable render(String viewName, Object data, Object request) {
        String html = renderView.execute(viewName, data).asString();
        return writer -> writer.write(html);
    }

    @Override
    public boolean exists(String viewName) {
        return exists.execute(viewName).asBoolean();
    }
}
